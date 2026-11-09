"""Rain radar cameras: the KNMI app's radar of the last hour, on a light and on a dark map."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    ATTRIBUTION,
    CONF_RADAR_MARKER,
    DOMAIN,
    RADAR_FRAMES,
    RADAR_FRAMES_URL,
    RADAR_INTERVAL,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from .coordinator import WeerberichtConfigEntry
from .radar_image import DARK, LIGHT, RadarStyle, build_loop

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeerberichtConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    frames = RadarFrames(hass)
    async_add_entities(
        [
            WeerberichtRadar(entry, frames, LIGHT, "radar", "radar"),
            WeerberichtRadar(entry, frames, DARK, "radar_dark", "radar-dark"),
        ]
    )


class RadarFrames:
    """The KNMI app's radar images of the last hour, shared by the radars of a location.

    The list of images is asked for at most once per RADAR_INTERVAL, and an
    image is downloaded only once. When the KNMI app can not be reached, the
    images already there are used, and it is tried again after the interval.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._session = async_get_clientsession(hass)
        self._images: dict[str, bytes] = {}
        self._frames: list[tuple[datetime, bytes]] = []
        self._checked: datetime | None = None
        self._lock = asyncio.Lock()

    async def async_frames(self) -> list[tuple[datetime, bytes]]:
        """The radar images of the last hour (local time, PNG), oldest first."""
        async with self._lock:
            now = dt_util.utcnow()
            if self._checked is None or now - self._checked >= timedelta(seconds=RADAR_INTERVAL):
                self._checked = now
                try:
                    self._frames = await self._async_fetch()
                except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, TypeError, ValueError) as err:
                    _LOGGER.warning("Rain radar: %s", err)
            return self._frames

    def _get(self, url: str):  # noqa: ANN202 - aiohttp's request context manager
        return self._session.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        )

    async def _async_fetch(self) -> list[tuple[datetime, bytes]]:
        async with self._get(RADAR_FRAMES_URL) as resp:
            resp.raise_for_status()
            listing = await resp.json(content_type=None)
        observed = [
            (dt_util.parse_datetime(frame["time"]), frame["links"]["detail"])
            for frame in listing["frames"]
            if "/observations/" in frame["links"]["detail"]
        ][-RADAR_FRAMES:]
        missing = [url for _, url in observed if url not in self._images]
        results = await asyncio.gather(*(self._async_image(url) for url in missing))
        for url, png in zip(missing, results):
            if png is not None:
                self._images[url] = png
        wanted = {url for _, url in observed}
        self._images = {url: png for url, png in self._images.items() if url in wanted}
        return [
            (dt_util.as_local(moment), self._images[url])
            for moment, url in observed
            if moment is not None and url in self._images
        ]

    async def _async_image(self, url: str) -> bytes | None:
        """One radar image; None when it can not be had now (tried again next time)."""
        try:
            async with self._get(url) as resp:
                if resp.status != 200:
                    _LOGGER.debug("Rain radar: HTTP %s for %s", resp.status, url)
                    return None
                return await resp.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Rain radar: %s for %s", err, url)
            return None


class WeerberichtRadar(Camera):
    """The rain radar of the last hour as an animated GIF, light or dark.

    Made from the KNMI app's radar images, with the time on every frame and,
    unless switched off in the options, a small house on the location. It is
    made only when a dashboard asks for it, and kept until a new radar image
    is there, so an idle dashboard costs nothing.
    """

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: WeerberichtConfigEntry,
        frames: RadarFrames,
        style: RadarStyle,
        translation_key: str,
        unique_suffix: str,
    ) -> None:
        super().__init__()
        # Camera sets image/jpeg in its __init__; a GIF says so, and is not
        # sent through the JPEG scaler when a card asks for a smaller size.
        self.content_type = "image/gif"
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}-{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="KNMI",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._frames = frames
        self._style = style
        self._image: bytes | None = None
        self._latest: datetime | None = None
        self._lock = asyncio.Lock()
        self._marker: tuple[float, float] | None = None
        if entry.options.get(CONF_RADAR_MARKER, True):
            self._marker = (entry.data[CONF_LATITUDE], entry.data[CONF_LONGITUDE])

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {
            "source": RADAR_FRAMES_URL,
            "radar_time": self._latest.isoformat() if self._latest else None,
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        async with self._lock:
            frames = await self._frames.async_frames()
            if not frames or (self._image is not None and frames[-1][0] == self._latest):
                return self._image
            try:
                credit = "Bron: KNMI" if self.hass.config.language.startswith("nl") else "Data source: KNMI"
                image = await self.hass.async_add_executor_job(
                    build_loop, frames, self._marker, self._style, credit
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Rain radar: could not draw the loop: %s", err)
                return self._image
            if image is not None:
                self._image = image
                self._latest = frames[-1][0]
            return self._image
