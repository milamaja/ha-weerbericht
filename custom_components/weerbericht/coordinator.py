"""Data coordinator: fetches the forecast and reshapes it for the entities."""
from __future__ import annotations

from datetime import datetime
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


class WeerberichtCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the KNMI app backend."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: WeerberichtClient,
        cell: str,
        region: str,
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
        # Dutch (the KNMI's own texts) unless English is chosen in the settings.
        self.language = entry.options.get(CONF_WARNING_LANGUAGE, "nl")
        self.rain: WeerberichtRainCoordinator | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            summary = await self.client.weather(self.cell, self.region)
            details: dict[str, dict[str, Any]] = {}
            for day in summary.get("daily", {}).get("forecast", []):
                date = day.get("date")
                if date:
                    details[date] = await self.client.weather_detail(
                        self.cell, self.region, date
                    )
        except WeerberichtError as err:
            raise UpdateFailed(str(err)) from err

        try:
            data = self._reshape(summary, details)
        except (KeyError, TypeError, ValueError) as err:
            raise UpdateFailed(f"unexpected response: {err!r}") from err

        # English warning texts: only looked up when English is chosen and the
        # KNMI app reports a warning (the MeteoAlarm feed is about 1 MB).
        data["alerts_en"] = None
        if self.language == "en" and (data["alerts"] or self._max_hourly_level(data) != "none"):
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

    def _meteoalarm_alerts(self, feed: dict[str, Any]) -> list[dict[str, str]]:
        """English yellow/orange/red warnings for this region that have not expired."""
        emma = REGION_EMMA.get(str(self.region))
        now = dt_util.utcnow()
        today = dt_util.now().date()
        out: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for warning in feed.get("warnings", []):
            alert = warning.get("alert") or {}
            if alert.get("msgType") == "Cancel":
                continue
            for info in alert.get("info") or []:
                if not str(info.get("language", "")).lower().startswith("en"):
                    continue
                codes = {
                    g.get("value")
                    for area in info.get("area") or []
                    for g in area.get("geocode") or []
                }
                if emma not in codes:
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
                out.append(
                    {
                        "level": level,
                        "title": event,
                        "description": f"Code {level}: {event[0].lower() + event[1:]}{span}",
                        "details": str(info.get("description") or "").strip(),
                    }
                )
        order = {"red": 0, "orange": 1, "yellow": 2}
        out.sort(key=lambda a: order[a["level"]])
        return out

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
        """Active KNMI warnings from the app, in Dutch."""
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
            "rain_start": start.isoformat() if start else None,
            "rain_end": end.isoformat() if end else None,
            "max_intensity": round(max((a for _, a in upcoming), default=0), 2),
            "radar_run": (self.data or {}).get("run"),
        }
