"""Config flow for the Burgers Zoo integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BurgersZooApiClient, BurgersZooError
from .const import (
    CONF_FORECAST_DAYS,
    CONF_LANGUAGE,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_LANGUAGE,
    DOMAIN,
    LANGUAGES,
    MAX_FORECAST_DAYS,
    MIN_FORECAST_DAYS,
    NAME,
    SINGLE_INSTANCE_UNIQUE_ID,
)


def build_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the language + forecast-days schema with the given defaults."""
    return vol.Schema(
        {
            vol.Required(
                CONF_LANGUAGE,
                default=defaults.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=LANGUAGES,
                    translation_key="language",
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_FORECAST_DAYS,
                default=defaults.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_FORECAST_DAYS,
                    max=MAX_FORECAST_DAYS,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


class BurgersZooConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Burgers Zoo config flow."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(SINGLE_INSTANCE_UNIQUE_ID)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = BurgersZooApiClient(session, user_input[CONF_LANGUAGE])
            try:
                await client.async_get_day(0)
            except BurgersZooError:
                errors["base"] = "cannot_connect"
            else:
                user_input[CONF_FORECAST_DAYS] = int(
                    user_input[CONF_FORECAST_DAYS]
                )
                return self.async_create_entry(title=NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=build_schema(user_input or {}),
            errors=errors,
        )
