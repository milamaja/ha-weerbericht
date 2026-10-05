"""Sensors: a few headline values from the forecast."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfPrecipitationDepth, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ALERT_LEVELS
from .coordinator import WeerberichtConfigEntry, WeerberichtCoordinator
from .entity import WeerberichtEntity


@dataclass(frozen=True, kw_only=True)
class WeerberichtSensorDescription(SensorEntityDescription):
    value_fn: Callable[[WeerberichtCoordinator], Any]
    attributes_fn: Callable[[WeerberichtCoordinator], dict[str, Any]] | None = None


def _current(c: WeerberichtCoordinator) -> dict[str, Any]:
    return (c.data or {}).get("current", {})


def _today(c: WeerberichtCoordinator) -> dict[str, Any]:
    return c.today() or {}


SENSORS: tuple[WeerberichtSensorDescription, ...] = (
    WeerberichtSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda c: _current(c).get("temperature"),
    ),
    WeerberichtSensorDescription(
        key="temperature_max_today",
        translation_key="temperature_max_today",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda c: _today(c).get("temperature"),
    ),
    WeerberichtSensorDescription(
        key="temperature_min_today",
        translation_key="temperature_min_today",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda c: _today(c).get("templow"),
    ),
    WeerberichtSensorDescription(
        key="precipitation_today",
        translation_key="precipitation_today",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda c: _today(c).get("precipitation"),
        attributes_fn=lambda c: {
            "probability": _today(c).get("precipitation_probability")
        },
    ),
    WeerberichtSensorDescription(
        key="sunshine_today",
        translation_key="sunshine_today",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:white-balance-sunny",
        value_fn=lambda c: _current(c).get("sunshine_hours_today"),
        attributes_fn=lambda c: {"description": _current(c).get("sunshine_text_today")},
    ),
    WeerberichtSensorDescription(
        key="uv_index",
        translation_key="uv_index",
        icon="mdi:sun-wireless",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _current(c).get("uv_index"),
        attributes_fn=lambda c: {"summary": _current(c).get("uv_summary")},
    ),
    WeerberichtSensorDescription(
        key="heat_index",
        translation_key="heat_index",
        icon="mdi:thermometer-alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _current(c).get("heat_index"),
    ),
    WeerberichtSensorDescription(
        key="alert_level",
        translation_key="alert_level",
        device_class=SensorDeviceClass.ENUM,
        options=ALERT_LEVELS,
        icon="mdi:alert",
        value_fn=lambda c: c.alert_level_24h(),
        attributes_fn=lambda c: {"alerts": (c.data or {}).get("alerts", [])},
    ),
    WeerberichtSensorDescription(
        key="alert_text",
        translation_key="alert_text",
        icon="mdi:alert-circle-outline",
        value_fn=lambda c: c.alert_text(),
        attributes_fn=lambda c: {"alerts": c.alerts()},
    ),
    WeerberichtSensorDescription(
        key="weather_text",
        translation_key="weather_text",
        icon="mdi:weather-partly-cloudy",
        value_fn=lambda c: c.weather_type_text((c.current_hour() or {}).get("weather_type")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeerberichtConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(WeerberichtSensor(entry, desc) for desc in SENSORS)


class WeerberichtSensor(WeerberichtEntity, SensorEntity):
    entity_description: WeerberichtSensorDescription

    def __init__(self, entry: WeerberichtConfigEntry, description: WeerberichtSensorDescription) -> None:
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}-{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator)
