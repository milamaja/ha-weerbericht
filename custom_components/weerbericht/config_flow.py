"""Config flow for Weerbericht."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import WeerberichtClient, WeerberichtError, grid_cell
from .const import ALERT_REGIONS, CONF_REGION, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WeerberichtConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for a name, a coordinate and the warning region."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            cell = grid_cell(user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE])
            if cell is None:
                errors["base"] = "outside_grid"
            else:
                await self.async_set_unique_id(f"{cell}-{user_input[CONF_REGION]}")
                self._abort_if_unique_id_configured()
                client = WeerberichtClient(async_get_clientsession(self.hass))
                try:
                    await client.weather(cell, user_input[CONF_REGION])
                except WeerberichtError as err:
                    _LOGGER.warning("KNMI app API check failed: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="KNMI"): str,
                vol.Required(
                    CONF_LATITUDE, default=self.hass.config.latitude
                ): cv.latitude,
                vol.Required(
                    CONF_LONGITUDE, default=self.hass.config.longitude
                ): cv.longitude,
                vol.Required(CONF_REGION): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=key, label=name)
                            for key, name in sorted(
                                ALERT_REGIONS.items(), key=lambda kv: kv[1]
                            )
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )
