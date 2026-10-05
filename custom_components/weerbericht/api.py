"""Minimal client for the KNMI app backend (api.app.knmi.cloud).

This is the same, keyless API the official KNMI weather app uses. KNMI has
published the app and this backend as open source (EUPL-1.2), but offers no
stability guarantee for it, unlike the KNMI Data Platform.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import (
    BASE_URL,
    GRID_NE_LAT,
    GRID_NE_LON,
    GRID_PREFIX,
    GRID_STEPS_LAT,
    GRID_STEPS_LON,
    GRID_SW_LAT,
    GRID_SW_LON,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class WeerberichtError(Exception):
    """Base error."""


class WeerberichtConnectionError(WeerberichtError):
    """Network or server problem."""


class WeerberichtNotFound(WeerberichtError):
    """No data for this cell."""


def grid_cell(latitude: float, longitude: float) -> str | None:
    """Return the forecast grid cell (for example "A512"), or None if outside."""
    if not (GRID_SW_LAT < latitude <= GRID_NE_LAT and GRID_SW_LON <= longitude < GRID_NE_LON):
        return None
    lat_mult = GRID_STEPS_LAT / (GRID_NE_LAT - GRID_SW_LAT)
    lon_mult = GRID_STEPS_LON / (GRID_NE_LON - GRID_SW_LON)
    lat_cell = int((GRID_NE_LAT - latitude) * lat_mult)
    lon_cell = int((longitude - GRID_SW_LON) * lon_mult)
    return f"{GRID_PREFIX}{lat_cell + lon_cell * GRID_STEPS_LAT}"


class WeerberichtClient:
    """Async client."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get(self, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{BASE_URL}/{endpoint}"
        try:
            async with self._session.get(
                url,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                if resp.status == 404:
                    raise WeerberichtNotFound(f"{endpoint}: no data for {params}")
                if resp.status >= 400:
                    body = await resp.text()
                    raise WeerberichtConnectionError(
                        f"{endpoint}: HTTP {resp.status}: {body[:200]}"
                    )
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WeerberichtConnectionError(f"{endpoint}: {err}") from err

    async def weather(self, cell: str, region: str) -> dict[str, Any]:
        """Summary: current values, 60 hourly and 7 daily forecast entries."""
        return await self._get("weather", {"location": cell, "region": region})

    async def weather_detail(self, cell: str, region: str, date: str) -> dict[str, Any]:
        """Per-day detail: precipitation chance, wind, sunshine, UV, 14-day outlook."""
        return await self._get(
            "weather/detail", {"location": cell, "region": region, "date": date}
        )
