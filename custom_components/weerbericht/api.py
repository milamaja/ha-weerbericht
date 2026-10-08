"""Minimal client for the KNMI app backend (api.app.knmi.cloud).

This is the same, keyless API the official KNMI weather app uses. KNMI has
published the app and this backend as open source (EUPL-1.2), but offers no
stability guarantee for it, unlike the KNMI Data Platform.
"""
from __future__ import annotations

import asyncio
import logging
import math
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
    METEOALARM_TIMEOUT,
    METEOALARM_URL,
    RADAR_ELLIPSOID,
    RADAR_LAT_TS,
    RADAR_NE,
    RADAR_PREFIX,
    RADAR_STEPS,
    RADAR_SW,
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


def radar_cell(latitude: float, longitude: float) -> str | None:
    """Return the radar grid cell (for example "B34908" for central Amsterdam) used by the rain graph, or None if outside.

    The app projects the location to polar stereographic coordinates (km) on the
    KNMI radar ellipsoid and looks the point up in a 1 km grid.
    """
    a, b = RADAR_ELLIPSOID
    e = math.sqrt(1 - (b * b) / (a * a))

    def t(phi: float) -> float:
        s = math.sin(phi)
        return math.tan(math.pi / 4 - phi / 2) / ((1 - e * s) / (1 + e * s)) ** (e / 2)

    pc = math.radians(RADAR_LAT_TS)
    mc = math.cos(pc) / math.sqrt(1 - e * e * math.sin(pc) ** 2)
    rho = a * mc * t(math.radians(latitude)) / t(pc)
    x = rho * math.sin(math.radians(longitude))
    y = -rho * math.cos(math.radians(longitude))
    (sw_y, sw_x), (ne_y, ne_x) = RADAR_SW, RADAR_NE
    if not (sw_y < y <= ne_y and sw_x <= x < ne_x):
        return None
    row = int((ne_y - y) * RADAR_STEPS[0] / (ne_y - sw_y))
    col = int((x - sw_x) * RADAR_STEPS[1] / (ne_x - sw_x))
    return f"{RADAR_PREFIX}{row + col * RADAR_STEPS[0]}"


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

    async def precipitation_run(self) -> str:
        """Time of the latest rain radar run (needed to ask for the rain graph)."""
        data = await self._get("precipitation/radar", {})
        return data["time"]

    async def precipitation_graph(self, cell: str, run: str) -> dict[str, Any]:
        """Rain intensity (mm/h) in 5-minute steps for a grid cell, two hours either side of the run."""
        return await self._get("precipitation/graph", {"location": cell, "time": run})

    async def meteoalarm(self) -> dict[str, Any]:
        """All current MeteoAlarm warnings for the Netherlands (large: about 1 MB)."""
        try:
            async with self._session.get(
                METEOALARM_URL,
                headers={"User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=METEOALARM_TIMEOUT),
            ) as resp:
                if resp.status >= 400:
                    raise WeerberichtConnectionError(f"meteoalarm: HTTP {resp.status}")
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise WeerberichtConnectionError(f"meteoalarm: {err}") from err
