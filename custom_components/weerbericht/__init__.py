"""Weerbericht: weather forecast from the KNMI app backend."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from aiohttp import web

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import WeerberichtClient, grid_cell
from .const import CONF_REGION, DOMAIN
from .coordinator import WeerberichtConfigEntry, WeerberichtCoordinator

PLATFORMS: list[Platform] = [Platform.WEATHER, Platform.SENSOR, Platform.CAMERA]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

CARD_URL = f"/{DOMAIN}/weerbericht-card.js"
CARD_FILE = Path(__file__).parent / "frontend" / "weerbericht-card.js"

_LOGGER = logging.getLogger(__name__)


class WeerberichtCardView(HomeAssistantView):
    """Serve the dashboard card without long-lived browser caching."""

    url = CARD_URL
    name = f"{DOMAIN}:card"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get(self, request: web.Request) -> web.Response:
        _LOGGER.debug(
            "Card requested (%s) by %s", request.query_string, request.headers.get("User-Agent")
        )
        body = await self._hass.async_add_executor_job(CARD_FILE.read_bytes)
        return web.Response(
            body=body,
            content_type="text/javascript",
            headers={"Cache-Control": "no-cache"},
        )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the Weerbericht dashboard card and load it in the frontend."""
    body = await hass.async_add_executor_job(CARD_FILE.read_bytes)
    # A new build gets a new URL, so browsers never run a stale copy.
    digest = hashlib.sha1(body).hexdigest()[:10]
    url = f"{CARD_URL}?v={digest}"
    hass.http.register_view(WeerberichtCardView(hass))
    # Loaded by the start page in up-to-date browsers...
    add_extra_js_url(hass, url)
    # ...and as a dashboard resource, which dashboards fetch live, so clients
    # holding a cached start page (the companion apps) load the card too.
    await _async_ensure_resource(hass, url)
    return True


def _storage_resources(hass: HomeAssistant):
    """The dashboard resource collection, or None in YAML resource mode."""
    data = hass.data.get(LOVELACE_DATA)
    # resource_mode exists since Home Assistant 2026.x; older versions use mode.
    mode = getattr(data, "resource_mode", getattr(data, "mode", None)) if data else None
    if data is None or mode != "storage":
        return None
    return data.resources


async def _async_ensure_resource(hass: HomeAssistant, url: str) -> None:
    resources = _storage_resources(hass)
    if resources is None:
        _LOGGER.debug("Dashboard resources are in YAML mode; add %s yourself", url)
        return
    try:
        await resources.async_get_info()  # loads the collection
        for item in resources.async_items():
            if item.get("url", "").split("?")[0] == CARD_URL:
                if item["url"] != url:
                    await resources.async_update_item(
                        item["id"], {"res_type": "module", "url": url}
                    )
                return
        await resources.async_create_item({"res_type": "module", "url": url})
    except Exception as err:  # noqa: BLE001 - the card still loads via the start page
        _LOGGER.warning("Could not register the Weerbericht card as a dashboard resource: %s", err)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the dashboard resource together with the last location."""
    if hass.config_entries.async_entries(DOMAIN):
        remaining = [e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id != entry.entry_id]
        if remaining:
            return
    resources = _storage_resources(hass)
    if resources is None:
        return
    try:
        await resources.async_get_info()
        for item in resources.async_items():
            if item.get("url", "").split("?")[0] == CARD_URL:
                await resources.async_delete_item(item["id"])
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not remove the Weerbericht card resource: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: WeerberichtConfigEntry) -> bool:
    """Set up a location."""
    cell = grid_cell(entry.data[CONF_LATITUDE], entry.data[CONF_LONGITUDE])
    if cell is None:
        raise ConfigEntryNotReady("location is outside the KNMI forecast grid")

    coordinator = WeerberichtCoordinator(
        hass,
        entry,
        WeerberichtClient(async_get_clientsession(hass)),
        cell,
        entry.data[CONF_REGION],
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WeerberichtConfigEntry) -> bool:
    """Unload a location."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
