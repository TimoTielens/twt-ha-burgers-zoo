"""API client for the Burgers Zoo weather endpoint."""
from __future__ import annotations

import asyncio

import aiohttp

from .const import API_TIMEOUT, API_URL_TEMPLATE, CULTURE_MAP, DEFAULT_LANGUAGE
from .models import DayData


class BurgersZooError(Exception):
    """Base error for the Burgers Zoo integration."""


class BurgersZooConnectionError(BurgersZooError):
    """Raised when the API cannot be reached."""


class BurgersZooApiError(BurgersZooError):
    """Raised when the API returns an unexpected status or payload."""


class BurgersZooApiClient:
    """Async client for the Burgers Zoo weather API."""

    def __init__(self, session: aiohttp.ClientSession, language: str) -> None:
        self._session = session
        self._culture = CULTURE_MAP.get(language, CULTURE_MAP[DEFAULT_LANGUAGE])

    async def async_get_day(self, day: int) -> DayData:
        """Fetch and parse a single forecast day."""
        url = API_URL_TEMPLATE.format(day=day, culture=self._culture)
        try:
            async with asyncio.timeout(API_TIMEOUT):
                response = await self._session.get(url)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BurgersZooConnectionError(
                f"Error connecting to Burgers Zoo API for day {day}: {err}"
            ) from err

        if response.status != 200:
            raise BurgersZooApiError(
                f"Burgers Zoo API returned status {response.status} for day {day}"
            )

        try:
            data = await response.json()
        except (aiohttp.ClientError, ValueError) as err:
            raise BurgersZooApiError(
                f"Could not parse Burgers Zoo API response for day {day}: {err}"
            ) from err

        return DayData.from_json(data)

    async def async_get_days(self, count: int) -> dict[int, DayData]:
        """Fetch days 0..count-1 concurrently."""
        results = await asyncio.gather(
            *(self.async_get_day(day) for day in range(count))
        )
        return dict(enumerate(results))
