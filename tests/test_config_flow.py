"""Tests for the Burgers Zoo config flow."""
from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.twt_ha_burgers_zoo.const import (
    CONF_FORECAST_DAYS,
    CONF_LANGUAGE,
    DOMAIN,
    SINGLE_INSTANCE_UNIQUE_ID,
)


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_api) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LANGUAGE: "nl", CONF_FORECAST_DAYS: 3},
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Burgers Zoo"
    assert result2["data"] == {CONF_LANGUAGE: "nl", CONF_FORECAST_DAYS: 3}


async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    from aioresponses import aioresponses

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    with aioresponses() as mocked:
        mocked.get(
            "https://www.burgerszoo.nl/api/weather/0?culture=nl-NL",
            status=500,
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_LANGUAGE: "nl", CONF_FORECAST_DAYS: 3},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_single_instance_aborts(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_updates_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api
) -> None:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        mock_config_entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_LANGUAGE: "en", CONF_FORECAST_DAYS: 5},
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {
        CONF_LANGUAGE: "en",
        CONF_FORECAST_DAYS: 5,
    }
