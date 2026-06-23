"""Tests for the Burgers Zoo integration setup/unload."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.twt_ha_burgers_zoo.coordinator import (
    BurgersZooDataUpdateCoordinator,
)


async def test_setup_and_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api,
) -> None:
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert isinstance(
        mock_config_entry.runtime_data, BurgersZooDataUpdateCoordinator
    )
    assert mock_config_entry.runtime_data.data[0].temperature == 30

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_on_api_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    from aioresponses import aioresponses

    mock_config_entry.add_to_hass(hass)
    with aioresponses() as mocked:
        mocked.get(
            "https://www.burgerszoo.nl/api/weather/0?culture=nl-NL",
            status=500,
            repeat=True,
        )
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
