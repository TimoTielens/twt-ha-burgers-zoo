"""Tests for the Burgers Zoo data update coordinator."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.twt_ha_burgers_zoo.api import BurgersZooConnectionError
from custom_components.twt_ha_burgers_zoo.coordinator import (
    BurgersZooDataUpdateCoordinator,
)
from custom_components.twt_ha_burgers_zoo.models import DayData


async def test_update_returns_indexed_data(hass: HomeAssistant) -> None:
    client = AsyncMock()
    client.async_get_days.return_value = {
        0: DayData.from_json({"temperature": 30}),
        1: DayData.from_json({"temperature": 28}),
    }
    coordinator = BurgersZooDataUpdateCoordinator(hass, client, forecast_days=2)

    data = await coordinator._async_update_data()

    client.async_get_days.assert_awaited_once_with(2)
    assert data[0].temperature == 30
    assert data[1].temperature == 28


async def test_update_wraps_errors_as_update_failed(hass: HomeAssistant) -> None:
    client = AsyncMock()
    client.async_get_days.side_effect = BurgersZooConnectionError("down")
    coordinator = BurgersZooDataUpdateCoordinator(hass, client, forecast_days=3)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
