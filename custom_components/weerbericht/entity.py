"""Shared entity base."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import WeerberichtConfigEntry, WeerberichtCoordinator


def device_info(entry: WeerberichtConfigEntry) -> DeviceInfo:
    """One device per configured location."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="KNMI",
        model="Weerbericht (KNMI app data)",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url="https://www.knmi.nl/nederland-nu/weer/verwachtingen",
    )


class WeerberichtEntity(CoordinatorEntity[WeerberichtCoordinator]):
    """Entity fed by the forecast coordinator."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, entry: WeerberichtConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        self._entry = entry
        self._attr_device_info = device_info(entry)
