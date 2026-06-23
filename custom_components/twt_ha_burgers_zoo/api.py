"""API client for the Burgers Zoo weather endpoint."""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from .const import API_TIMEOUT, API_URL_TEMPLATE, CULTURE_MAP, DEFAULT_LANGUAGE
from .models import DayData

_LOGGER = logging.getLogger(__name__)


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
                async with self._session.get(url) as response:
                    if response.status != 200:
                        raise BurgersZooApiError(
                            f"Burgers Zoo API returned status {response.status} for day {day}"
                        )
                    try:
                        data = await response.json()
                        return DayData.from_json(data)
                    except (aiohttp.ClientError, ValueError, TypeError, AttributeError, KeyError) as err:
                        raise BurgersZooApiError(
                            f"Could not parse Burgers Zoo API response for day {day}: {err}"
                        ) from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise BurgersZooConnectionError(
                f"Error connecting to Burgers Zoo API for day {day}: {err}"
            ) from err

    async def async_get_days(self, count: int) -> dict[int, DayData]:
        """Fetch days 0..count-1 concurrently, tolerating individual day failures."""
        results = await asyncio.gather(
            *(self.async_get_day(day) for day in range(count)),
            return_exceptions=True,
        )
        days = {i: r for i, r in enumerate(results) if not isinstance(r, Exception)}
        if not days:
            # every day failed — surface a single error so the coordinator marks unavailable
            first_error = next(r for r in results if isinstance(r, Exception))
            raise first_error
        # log the failed days at warning level
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                _LOGGER.warning("Burgers Zoo: failed to fetch day %s: %s", i, r)
        return days
