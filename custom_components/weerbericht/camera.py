"""Rain radar camera: the animated radar loop published on knmi.nl."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    ATTRIBUTION,
    DOMAIN,
    RADAR_INTERVAL,
    RADAR_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from .coordinator import WeerberichtConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeerberichtConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WeerberichtRadar(hass, entry)])


class WeerberichtRadar(Camera):
    """Serves the national precipitation radar loop (GIF, refreshed every 5 minutes).

    The image is fetched on demand and cached for RADAR_INTERVAL, so an idle
    dashboard costs nothing and a busy one still makes at most one request per
    interval.
    """

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_translation_key = "radar"
    _attr_content_type = "image/gif"

    def __init__(self, hass: HomeAssistant, entry: WeerberichtConfigEntry) -> None:
        super().__init__()
        self._session = async_get_clientsession(hass)
        self._attr_unique_id = f"{entry.entry_id}-radar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="KNMI",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._image: bytes | None = None
        self._fetched = None
        self._last_modified: str | None = None
        self._lock = asyncio.Lock()

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {"source": RADAR_URL, "last_modified": self._last_modified}

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        async with self._lock:
            now = dt_util.utcnow()
            if self._image is not None and self._fetched is not None:
                if now - self._fetched < timedelta(seconds=RADAR_INTERVAL):
                    return self._image
            headers = {"User-Agent": USER_AGENT}
            if self._last_modified:
                headers["If-Modified-Since"] = self._last_modified
            try:
                async with self._session.get(
                    RADAR_URL,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ) as resp:
                    if resp.status == 304 and self._image is not None:
                        self._fetched = now
                        return self._image
                    if resp.status != 200:
                        _LOGGER.warning("Radar image: HTTP %s", resp.status)
                        return self._image
                    self._image = await resp.read()
                    self._last_modified = resp.headers.get("Last-Modified")
                    self._fetched = now
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.warning("Radar image: %s", err)
            return self._image
