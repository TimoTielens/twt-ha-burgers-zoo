"""Data update coordinator for the Burgers Zoo integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BurgersZooApiClient, BurgersZooError
from .const import DOMAIN, UPDATE_INTERVAL_HOURS
from .models import DayData

_LOGGER = logging.getLogger(__name__)


class BurgersZooDataUpdateCoordinator(DataUpdateCoordinator[dict[int, DayData]]):
    """Coordinates fetching all configured forecast days."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BurgersZooApiClient,
        forecast_days: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )
        self.client = client
        self.forecast_days = forecast_days

    async def _async_update_data(self) -> dict[int, DayData]:
        """Fetch all configured forecast days from the API."""
        try:
            return await self.client.async_get_days(self.forecast_days)
        except BurgersZooError as err:
            raise UpdateFailed(str(err)) from err
