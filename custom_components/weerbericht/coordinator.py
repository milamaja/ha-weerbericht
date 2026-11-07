"""Data coordinator: fetches the forecast and reshapes it for the entities."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import WeerberichtClient, WeerberichtError
from .const import (
    ALERT_LEVELS,
    CONDITION_MAP,
    CONF_WARNING_LANGUAGE,
    DOMAIN,
    NIGHT_CODES,
    NO_ALERT_TEXT,
    RAIN_INTERVAL,
    REGION_EMMA,
    UPDATE_INTERVAL,
    WEATHER_TYPE_TEXT,
)

_LOGGER = logging.getLogger(__name__)

type WeerberichtConfigEntry = ConfigEntry["WeerberichtCoordinator"]


def _percent(chance: Any) -> int | None:
    """The app reports chances as a 0..1 fraction; return a percentage."""
    if chance is None:
        return None
    try:
        value = float(chance)
    except (TypeError, ValueError):
        return None
    if value <= 1.0:
        value *= 100
    return int(round(value))


def _local_midnight(iso: str) -> datetime:
    """Daily entries carry 00:00Z; make them local midnight of that date."""
    dt = dt_util.as_local(datetime.fromisoformat(iso))
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _condition(code: Any) -> str | None:
    return CONDITION_MAP.get(code) if isinstance(code, int) else None


def _max_alert(levels: list[str]) -> str:
    best = 0
    for level in levels:
        if level in ALERT_LEVELS:
            best = max(best, ALERT_LEVELS.index(level))
    return ALERT_LEVELS[best]


def _inside(lat: float, lon: float, ring: list[tuple[float, float]]) -> bool:
    """Is the point inside the polygon (a list of (lat, lon) corners)? Ray casting."""
    inside = False
    j = len(ring) - 1
    for i, (lat_i, lon_i) in enumerate(ring):
        lat_j, lon_j = ring[j]
        if (lat_i > lat) != (lat_j > lat) and lon < (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i) + lon_i:
            inside = not inside
        j = i
    return inside


def _cap_polygon(text: str) -> list[tuple[float, float]]:
    """A CAP polygon ("lat,lon lat,lon ...", as MeteoAlarm uses) as (lat, lon) corners."""
    corners: list[tuple[float, float]] = []
    for pair in str(text).split():
        lat, _, lon = pair.partition(",")
        try:
            corners.append((float(lat), float(lon)))
        except ValueError:
            continue
    return corners


_NL_DAYS = ["ma", "di", "wo", "do", "vr", "za", "zo"]


def _when(moment: datetime, language: str) -> str:
    """A warning time as the KNMI app says it: 15:00, tomorrow 03:00, or with the day."""
    local = dt_util.as_local(moment)
    days = (local.date() - dt_util.now().date()).days
    if days == 0:
        return local.strftime("%H:%M")
    if days == 1:
        return ("tomorrow " if language == "en" else "morgen ") + local.strftime("%H:%M")
    if language == "en":
        return local.strftime("%a %d %b %H:%M")
    return f"{_NL_DAYS[local.weekday()]} {local.day} {local.strftime('%H:%M')}"


class WeerberichtCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the KNMI app backend."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: WeerberichtClient,
        cell: str,
        region: str,
        latitude: float,
        longitude: float,
        place: tuple[str, str] | None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.title}",
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.cell = cell
        self.region = region
        self.latitude = latitude
        self.longitude = longitude
        # BAG place code and name for the local warnings; None outside the Netherlands.
        self.locality, self.locality_name = place if place else (None, None)
        # Dutch (the KNMI's own texts) unless English is chosen in the settings.
        self.language = entry.options.get(CONF_WARNING_LANGUAGE, "nl")
        self.rain: WeerberichtRainCoordinator | None = None
        # Full texts of local warnings, by warning id (they do not change).
        self._local_texts: dict[str, dict[str, Any]] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            summary = await self.client.weather(self.cell, self.region, self.locality)
            details: dict[str, dict[str, Any]] = {}
            for day in summary.get("daily", {}).get("forecast", []):
                date = day.get("date")
                if date:
                    details[date] = await self.client.weather_detail(
                        self.cell, self.region, date, self.locality
                    )
        except WeerberichtError as err:
            raise UpdateFailed(str(err)) from err

        try:
            data = self._reshape(summary, details)
        except (KeyError, TypeError, ValueError) as err:
            raise UpdateFailed(f"unexpected response: {err!r}") from err
        data["local_alerts"] = await self._local_alerts(summary.get("localAlerts") or [])

        # English warning texts: only looked up when English is chosen and the
        # KNMI app reports a warning (the MeteoAlarm feed is about 1 MB).
        data["alerts_en"] = None
        if self.language == "en" and (
            data["alerts"] or data["local_alerts"] or self._max_hourly_level(data) != "none"
        ):
            try:
                data["alerts_en"] = self._meteoalarm_alerts(await self.client.meteoalarm())
            except WeerberichtError as err:
                _LOGGER.warning("English warning texts unavailable: %s", err)
            except (KeyError, TypeError, ValueError) as err:
                _LOGGER.warning("Unexpected MeteoAlarm data: %r", err)
        return data

    @staticmethod
    def _max_hourly_level(data: dict[str, Any]) -> str:
        return _max_alert([h.get("alert_level", "none") for h in data.get("hourly", [])[:24]])

    async def _local_alerts(self, items: list[Any]) -> list[dict[str, Any]]:
        """The local warnings for this place, with the KNMI's headline and texts.

        The weather call only gives level, times and a short explanation ("Dichte
        mist"); the full text is fetched once per warning.
        """
        out: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            alert_id = str(item["id"])
            if alert_id not in self._local_texts:
                try:
                    full = await self.client.local_alert(alert_id)
                except WeerberichtError as err:
                    _LOGGER.debug("Text of local warning %s unavailable: %s", alert_id, err)
                    full = None
                if isinstance(full, dict) and str(full.get("id")) == alert_id:
                    self._local_texts[alert_id] = {
                        "headline": str(full.get("headline") or "").strip(),
                        "description": str(full.get("description") or "").strip(),
                        "detailed": str(full.get("detailedDescription") or "").strip(),
                    }
            text = self._local_texts.get(alert_id, {})
            out.append(
                {
                    "id": alert_id,
                    "level": str(item.get("level") or "none").lower(),
                    "onset": item.get("onset"),
                    "expires": item.get("expires"),
                    "explanation": str(item.get("explanation") or "").strip(),
                    "headline": text.get("headline", ""),
                    "description": text.get("description", ""),
                    "detailed": text.get("detailed", ""),
                }
            )
        current = {a["id"] for a in out}
        self._local_texts = {k: v for k, v in self._local_texts.items() if k in current}
        return out

    def _meteoalarm_alerts(self, feed: dict[str, Any]) -> list[dict[str, str]]:
        """English yellow/orange/red warnings for this location that have not expired.

        Province warnings carry the region's EMMA code; local warnings (since
        November 2026) only a polygon, so those count when the location is inside.
        """
        emma = REGION_EMMA.get(str(self.region))
        now = dt_util.utcnow()
        today = dt_util.now().date()
        out: list[dict[str, str]] = []
        starts: list[datetime] = []
        seen: set[tuple[str, str, str]] = set()
        for warning in feed.get("warnings", []):
            alert = warning.get("alert") or {}
            if alert.get("msgType") == "Cancel":
                continue
            for info in alert.get("info") or []:
                if not str(info.get("language", "")).lower().startswith("en"):
                    continue
                areas = info.get("area") or []
                codes = {g.get("value") for area in areas for g in area.get("geocode") or []}
                polygons = [
                    _cap_polygon(p)
                    for area in areas
                    for p in (area.get("polygon") if isinstance(area.get("polygon"), list) else [area.get("polygon") or ""])
                ]
                in_area = any(
                    len(ring) >= 3 and _inside(self.latitude, self.longitude, ring) for ring in polygons
                )
                if emma not in codes and not in_area:
                    continue
                level = ""
                for param in info.get("parameter") or []:
                    if param.get("valueName") == "awareness_level":
                        parts = [x.strip() for x in str(param.get("value", "")).split(";")]
                        level = parts[1].lower() if len(parts) > 1 else ""
                if level not in ("yellow", "orange", "red"):
                    continue
                onset = dt_util.parse_datetime(info.get("onset") or info.get("effective") or "")
                expires = dt_util.parse_datetime(info.get("expires") or "")
                if expires is None or expires <= now:
                    continue

                def when(moment):
                    local = dt_util.as_local(moment)
                    if local.date() == today:
                        return local.strftime("%H:%M")
                    if (local.date() - today).days == 1:
                        return "tomorrow " + local.strftime("%H:%M")
                    return local.strftime("%a %d %b %H:%M")

                event = str(info.get("event") or "weather warning").strip()
                span = f" from {when(onset)} until {when(expires)}" if onset else f" until {when(expires)}"
                key = (level, event.lower(), span)
                if key in seen:
                    continue
                seen.add(key)
                starts.append(onset or expires)
                out.append(
                    {
                        "level": level,
                        "title": event,
                        "description": f"Code {level}: {event[0].lower() + event[1:]}{span}",
                        "details": str(info.get("description") or "").strip(),
                    }
                )
        # Highest level first, then in time order, like the KNMI's Dutch texts.
        order = {"red": 0, "orange": 1, "yellow": 2}
        ranked = sorted(zip(out, starts), key=lambda pair: (order[pair[0]["level"]], pair[1]))
        return [alert for alert, _ in ranked]

    def _reshape(
        self, summary: dict[str, Any], details: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        hourly: list[dict[str, Any]] = []
        for h in summary.get("hourly", {}).get("forecast", []):
            wind = h.get("wind") or {}
            precip = h.get("precipitation") or {}
            hourly.append(
                {
                    "datetime": datetime.fromisoformat(h["dateTime"]),
                    "temperature": h.get("temperature"),
                    "precipitation": precip.get("amount"),
                    "precipitation_probability": _percent(precip.get("chance")),
                    # Home Assistant's weather card draws its own moon variants
                    # for forecast entries marked is_daytime False.
                    "condition": _condition(h.get("weatherType")),
                    "raw_condition": _condition(h.get("weatherType")),
                    "is_daytime": h.get("weatherType") not in NIGHT_CODES,
                    "weather_type": h.get("weatherType"),
                    "wind_speed": wind.get("speed"),
                    "wind_gust_speed": wind.get("gusts"),
                    "wind_bearing": wind.get("degree"),
                    "beaufort": wind.get("beaufort"),
                    "alert_level": h.get("alertLevel", "none"),
                    "heat_index": h.get("heatIndex"),
                }
            )

        daily: list[dict[str, Any]] = []
        seen_dates: set[str] = set()
        # The app's days are UTC dates; just after midnight local time the first
        # one is still yesterday. Never show a day that is already over.
        today_local = dt_util.now().date()
        for d in summary.get("daily", {}).get("forecast", []):
            date = d["date"]
            seen_dates.add(date[:10])
            if _local_midnight(date).date() < today_local:
                continue
            detail = details.get(date, {})
            temp = d.get("temperature") or {}
            precip = d.get("precipitation") or {}
            wind = detail.get("wind") or {}
            chance = (detail.get("precipitationChance") or {}).get(
                "chance", precip.get("chance")
            )
            uv = detail.get("uvIndex") or {}
            daily.append(
                {
                    "datetime": _local_midnight(date),
                    "temperature": temp.get("max"),
                    "templow": temp.get("min"),
                    "precipitation": precip.get("amount"),
                    "precipitation_probability": _percent(chance),
                    "condition": _condition(d.get("weatherType")),
                    "weather_type": d.get("weatherType"),
                    "wind_speed": wind.get("speed"),
                    "wind_gust_speed": wind.get("gusts"),
                    "wind_bearing": wind.get("degree"),
                    "uv_index": uv.get("value"),
                    "sunshine_hours": (detail.get("sunshine") or {}).get("hours"),
                    "alert_level": _max_alert(d.get("alertLevels") or []),
                    "extended": False,
                }
            )

        # Days 8 to 15 come from the 14-day outlook arrays (temperature and
        # precipitation only, no weather type).
        any_detail = next(iter(details.values()), {})
        outlook = any_detail.get("daily") or {}
        t = outlook.get("temperature") or {}
        p = outlook.get("precipitation") or {}
        p_by_date = dict(zip(p.get("dates", []), p.get("amounts", [])))
        for date, tmin, tmax in zip(
            t.get("dates", []), t.get("minTemperatures", []), t.get("maxTemperatures", [])
        ):
            if date[:10] in seen_dates or _local_midnight(date).date() < today_local:
                continue
            daily.append(
                {
                    "datetime": _local_midnight(date),
                    # Whole degrees, like the KNMI app and the first 7 days.
                    "temperature": round(tmax) if tmax is not None else None,
                    "templow": round(tmin) if tmin is not None else None,
                    "precipitation": round(p_by_date[date], 1) if date in p_by_date else None,
                    "extended": True,
                }
            )

        summaries = summary.get("summaries") or []
        current_temp = summaries[0].get("temperature") if summaries else None
        wind = summary.get("wind") or {}
        sun = summary.get("sun") or {}
        uv = summary.get("uvIndex") or {}
        today_detail = next(iter(details.values()), {})
        sunshine = today_detail.get("sunshine") or {}

        return {
            "current": {
                "temperature": current_temp,
                "wind_speed": wind.get("speed"),
                "wind_gust_speed": wind.get("gusts"),
                "wind_bearing": wind.get("degree"),
                "wind_source": wind.get("source"),
                "beaufort": wind.get("beaufort"),
                "uv_index": uv.get("value"),
                "uv_summary": uv.get("summary"),
                "heat_index": summary.get("heatIndex"),
                "sunrise": sun.get("sunrise"),
                "sunset": sun.get("sunset"),
                "sunshine_hours_today": sunshine.get("hours"),
                "sunshine_text_today": sunshine.get("description"),
            },
            "alerts": summary.get("alerts") or [],
            "hourly": hourly,
            "daily": daily,
            "fetched": dt_util.utcnow(),
        }

    # Helpers used by entities -------------------------------------------------

    def current_hour(self) -> dict[str, Any] | None:
        """The hourly entry that covers now (or the first future one)."""
        now = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
        hours = self.data.get("hourly", []) if self.data else []
        for h in hours:
            if h["datetime"] >= now:
                return h
        return hours[-1] if hours else None

    def today(self) -> dict[str, Any] | None:
        """Today's daily entry."""
        days = self.data.get("daily", []) if self.data else []
        today = dt_util.now().date()
        for d in days:
            if d["datetime"].date() == today:
                return d
        return days[0] if days else None

    def alerts(self) -> list[dict[str, str]]:
        """Active warnings as {level, description}, in the chosen language."""
        data = self.data or {}
        knmi = self._knmi_alerts()
        if self.language != "en":
            return knmi
        english = data.get("alerts_en")
        if english:
            return [
                {"level": a["level"], "description": a["description"], "details": a.get("details", "")}
                for a in english
            ]
        # No matching English text (yet): describe the KNMI level in English.
        return [
            {"level": a["level"], "description": f"Code {a['level']} weather warning"}
            for a in knmi
            if a["level"] != "none"
        ]

    def _knmi_alerts(self) -> list[dict[str, str]]:
        """Active KNMI warnings from the app, in Dutch: per province and local."""
        out: list[dict[str, str]] = []
        for a in (self.data or {}).get("alerts", []):
            if not isinstance(a, dict):
                continue
            description = str(a.get("description") or a.get("title") or "").strip()
            level = str(a.get("level") or "none").lower()
            if description:
                out.append(
                    {"level": level if level in ALERT_LEVELS else "none", "description": description}
                )
        now = dt_util.utcnow()
        for a in (self.data or {}).get("local_alerts", []):
            expires = dt_util.parse_datetime(a.get("expires") or "")
            if expires is not None and expires <= now:
                continue
            onset = dt_util.parse_datetime(a.get("onset") or "")
            title = (a.get("headline") or a.get("explanation") or "").removesuffix(".")
            if not title:
                continue
            span = ""
            if expires is not None:
                span = (f", van {_when(onset, 'nl')} tot {_when(expires, 'nl')}"
                        if onset is not None and onset > now else f", tot {_when(expires, 'nl')}")
            details = " ".join(t for t in (a.get("description"), a.get("detailed")) if t)
            level = a["level"] if a["level"] in ALERT_LEVELS else "none"
            if any(o["description"].startswith(title) and o["level"] == level for o in out):
                continue
            out.append({"level": level, "description": title + span, "details": details})
        return out

    def alert_level_24h(self) -> str:
        """Highest alert level among active warnings and the next 24 hours."""
        data = self.data or {}
        levels = [h.get("alert_level", "none") for h in data.get("hourly", [])[:24]]
        levels.extend(a["level"] for a in self._knmi_alerts())
        return _max_alert(levels)

    def alert_text(self) -> str:
        """Description of the first active warning, or a fixed 'none' text."""
        alerts = self.alerts()
        if not alerts:
            return NO_ALERT_TEXT.get(self.language, NO_ALERT_TEXT["nl"])
        return ". ".join(a["description"].removesuffix(".") for a in alerts)[:255]

    def is_night(self) -> bool:
        """True between sunset and sunrise (from the app's sun times), or for a night code."""
        hour = self.current_hour() or {}
        if hour.get("weather_type") in NIGHT_CODES:
            return True
        current = (self.data or {}).get("current", {})
        try:
            sunrise = datetime.fromisoformat(current["sunrise"])
            sunset = datetime.fromisoformat(current["sunset"])
        except (KeyError, TypeError, ValueError):
            return False
        now = dt_util.utcnow()
        return not sunrise <= now < sunset

    @staticmethod
    def weather_type_text(code: Any) -> str | None:
        """Dutch description of a KNMI weather type code."""
        return WEATHER_TYPE_TEXT.get(code) if isinstance(code, int) else None


class WeerberichtRainCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the rain graph of the KNMI app: expected rain for the next two hours.

    Polls only while a rain sensor is enabled (a coordinator without listeners
    does not schedule updates).
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: WeerberichtClient, cell: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.title} rain",
            update_interval=RAIN_INTERVAL,
        )
        self.client = client
        self.cell = cell

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            run = await self.client.precipitation_run()
            graph = await self.client.precipitation_graph(self.cell, run)
            precip = graph["precipitation"]
            points = [
                (datetime.fromisoformat(t), float(a or 0))
                for t, a in zip(precip["times"], precip["amounts"])
            ]
        except WeerberichtError as err:
            raise UpdateFailed(str(err)) from err
        except (KeyError, TypeError, ValueError) as err:
            raise UpdateFailed(f"unexpected rain graph: {err!r}") from err
        return {"run": run, "points": points}

    def upcoming(self) -> list[tuple[datetime, float]]:
        """The 5-minute steps from the current one onwards."""
        points = (self.data or {}).get("points", [])
        now = dt_util.utcnow()
        current = [i for i, (t, _) in enumerate(points) if t <= now]
        return points[current[-1] if current else 0:]

    def past(self, minutes: int = 60) -> list[tuple[datetime, float]]:
        """The 5-minute steps of the last hour, before the current one."""
        points = (self.data or {}).get("points", [])
        now = dt_util.utcnow()
        current = [t for t, _ in points if t <= now]
        if not current:
            return []
        start = current[-1] - timedelta(minutes=minutes)
        return [(t, a) for t, a in points if start <= t < current[-1]]

    def intensity_now(self) -> float | None:
        upcoming = self.upcoming()
        return round(upcoming[0][1], 2) if upcoming else None

    def expected_mm(self) -> float | None:
        """Total rain expected over the remaining steps (intensity x 5 minutes)."""
        upcoming = self.upcoming()
        if not upcoming:
            return None
        return round(sum(a for _, a in upcoming) / 12, 1)

    def attributes(self) -> dict[str, Any]:
        upcoming = self.upcoming()
        wet = [t for t, a in upcoming if a > 0]
        start = end = None
        if wet:
            start = wet[0]
            # End of the first shower: the first dry step after it starts.
            after = [t for t, a in upcoming if t > start and a == 0]
            end = after[0] if after else None
        return {
            "forecast": [
                {"datetime": t.isoformat(), "intensity": round(a, 2)} for t, a in upcoming
            ],
            "past": [
                {"datetime": t.isoformat(), "intensity": round(a, 2)} for t, a in self.past()
            ],
            "rain_start": start.isoformat() if start else None,
            "rain_end": end.isoformat() if end else None,
            "max_intensity": round(max((a for _, a in upcoming), default=0), 2),
            "radar_run": (self.data or {}).get("run"),
        }
