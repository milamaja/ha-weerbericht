"""Weather entity."""
from __future__ import annotations

from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import NIGHT_ICONS
from .coordinator import WeerberichtConfigEntry
from .entity import WeerberichtEntity

FORECAST_KEYS = (
    "datetime",
    "condition",
    "temperature",
    "templow",
    "precipitation",
    "precipitation_probability",
    "wind_speed",
    "wind_gust_speed",
    "wind_bearing",
    "uv_index",
    "is_daytime",
    "weather_type",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeerberichtConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WeerberichtWeather(entry)])


def _forecast(item: dict[str, Any]) -> Forecast:
    out: dict[str, Any] = {}
    for key in FORECAST_KEYS:
        value = item.get(key)
        if value is None:
            continue
        out[key] = value.isoformat() if key == "datetime" else value
    return Forecast(**out)  # type: ignore[typeddict-item]


class WeerberichtWeather(WeerberichtEntity, WeatherEntity):
    """Current values plus daily and hourly forecasts, as the KNMI app shows them."""

    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, entry: WeerberichtConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}-weather"

    @property
    def _current(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("current", {})

    @property
    def condition(self) -> str | None:
        """The KNMI condition; a clear sky after sunset is clear-night."""
        hour = self.coordinator.current_hour()
        condition = hour.get("raw_condition") if hour else None
        if condition == "sunny" and self.coordinator.is_night():
            return "clear-night"
        return condition

    @property
    def icon(self) -> str | None:
        """Moon icons after sunset, like the KNMI app (tiles, pickers, history)."""
        if not self.coordinator.is_night():
            return None
        hour = self.coordinator.current_hour() or {}
        return NIGHT_ICONS.get(hour.get("raw_condition") or "")

    @property
    def native_temperature(self) -> float | None:
        temp = self._current.get("temperature")
        if temp is None:
            hour = self.coordinator.current_hour()
            temp = hour.get("temperature") if hour else None
        return temp

    @property
    def native_wind_speed(self) -> float | None:
        return self._current.get("wind_speed")

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self._current.get("wind_gust_speed")

    @property
    def wind_bearing(self) -> float | None:
        return self._current.get("wind_bearing")

    @property
    def uv_index(self) -> float | None:
        return self._current.get("uv_index")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        hour = self.coordinator.current_hour() or {}
        today = self.coordinator.today() or {}
        return {
            "weather_type": hour.get("weather_type"),
            "raw_condition": hour.get("raw_condition"),
            "night": self.coordinator.is_night(),
            "today_high": today.get("temperature"),
            "today_low": today.get("templow"),
            "weather_text": self.coordinator.weather_type_text(hour.get("weather_type")),
            "wind_source": self._current.get("wind_source"),
            "beaufort": self._current.get("beaufort"),
            "heat_index": self._current.get("heat_index"),
            "sunrise": self._current.get("sunrise"),
            "sunset": self._current.get("sunset"),
            "sunshine_hours_today": self._current.get("sunshine_hours_today"),
            "precipitation_today": today.get("precipitation"),
            "precipitation_probability_today": today.get("precipitation_probability"),
            "alert_level": self.coordinator.alert_level_24h(),
            "alert_text": self.coordinator.alert_text() if self.coordinator.alerts() else None,
            "uv_summary": self._current.get("uv_summary"),
            "sunshine_text_today": self._current.get("sunshine_text_today"),
            "grid_cell": self.coordinator.cell,
            "region": self.coordinator.region,
        }

    async def async_forecast_daily(self) -> list[Forecast] | None:
        days = (self.coordinator.data or {}).get("daily") or []
        return [_forecast(d) for d in days] or None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        hour = self.coordinator.current_hour()
        if hour is None:
            return None
        hours = (self.coordinator.data or {}).get("hourly") or []
        return [_forecast(h) for h in hours if h["datetime"] >= hour["datetime"]] or None
