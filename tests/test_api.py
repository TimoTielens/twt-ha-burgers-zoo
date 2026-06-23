"""Tests for the Burgers Zoo API client."""
from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.twt_ha_burgers_zoo.api import (
    BurgersZooApiClient,
    BurgersZooApiError,
    BurgersZooConnectionError,
)


def _url(day: int, culture: str = "nl-NL") -> str:
    return f"https://www.burgerszoo.nl/api/weather/{day}?culture={culture}"


async def test_async_get_day_parses_payload(full_day_payload: dict) -> None:
    async with aiohttp.ClientSession() as session:
        client = BurgersZooApiClient(session, "nl")
        with aioresponses() as mocked:
            mocked.get(_url(0), payload=full_day_payload)
            day = await client.async_get_day(0)
    assert day.temperature == 30
    assert day.business_hours.user_friendly_text == "09:00 tot 18:00"


async def test_async_get_day_uses_configured_culture(full_day_payload: dict) -> None:
    async with aiohttp.ClientSession() as session:
        client = BurgersZooApiClient(session, "de")
        with aioresponses() as mocked:
            mocked.get(_url(0, "de-DE"), payload=full_day_payload)
            day = await client.async_get_day(0)
    assert day.temperature == 30


async def test_async_get_days_returns_indexed_dict(full_day_payload: dict) -> None:
    async with aiohttp.ClientSession() as session:
        client = BurgersZooApiClient(session, "nl")
        with aioresponses() as mocked:
            for i in range(3):
                mocked.get(_url(i), payload=full_day_payload)
            days = await client.async_get_days(3)
    assert set(days.keys()) == {0, 1, 2}
    assert all(d.temperature == 30 for d in days.values())


async def test_non_200_raises_api_error() -> None:
    async with aiohttp.ClientSession() as session:
        client = BurgersZooApiClient(session, "nl")
        with aioresponses() as mocked:
            mocked.get(_url(0), status=500)
            with pytest.raises(BurgersZooApiError):
                await client.async_get_day(0)


async def test_connection_failure_raises_connection_error() -> None:
    async with aiohttp.ClientSession() as session:
        client = BurgersZooApiClient(session, "nl")
        with aioresponses() as mocked:
            mocked.get(_url(0), exception=aiohttp.ClientConnectionError("boom"))
            with pytest.raises(BurgersZooConnectionError):
                await client.async_get_day(0)
