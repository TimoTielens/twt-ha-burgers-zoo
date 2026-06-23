"""Shared fixtures for Burgers Zoo tests."""
from __future__ import annotations

from collections.abc import Generator

import pytest
from aioresponses import aioresponses
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.twt_ha_burgers_zoo.const import (
    CONF_FORECAST_DAYS,
    CONF_LANGUAGE,
    DOMAIN,
    SINGLE_INSTANCE_UNIQUE_ID,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def full_day_payload() -> dict:
    """A complete day-0 payload as returned by the API."""
    return {
        "temperature": 30,
        "iconUrl": "FullSun",
        "suggestion": {
            "ecoDisplayTitle": "Ontdek de Oost-Afrikaanse savanne!",
            "ecoDisplaySlogan": "In één dag op wereldreis!",
            "ecoDisplayBlockTitle": "Tip! Ga op safari op onze savannevlakte",
            "content": "<p>{{dayText}} wordt het {{temperatureText}} graden: ideaal weer...</p>",
            "button": {
                "name": "Bezoek de savannevlakte",
                "target": None,
                "url": "https://www.burgerszoo.nl/reserveren",
            },
            "ecoDisplay": "safari",
            "vimeoUrl": "",
            "vimeoUrlMobile": "",
            "primaryHeaderVideo": "",
            "primaryHeaderVideoMobile": "",
            "headerVideo": "/media/jcadvkml/safari-1-2-small.mp4",
            "headerVideoMobile": "/media/mjojmyus/safari-1-2-small.mp4",
            "headerImage": "/media/djnj14z5/safari-still.jpg?width=1920",
            "headerImageMobile": None,
        },
        "businessHours": {
            "isOpen": True,
            "openTime": "09:00:00",
            "closeTime": "18:00:00",
            "userFriendlyText": "09:00 tot 18:00",
        },
        "chanceOfRain": 10,
    }


@pytest.fixture
def empty_suggestion_payload() -> dict:
    """A payload where suggestion exists but all its fields are null (day 5)."""
    return {
        "temperature": None,
        "iconUrl": None,
        "suggestion": {
            "ecoDisplayTitle": None,
            "ecoDisplaySlogan": None,
            "ecoDisplayBlockTitle": None,
            "content": None,
            "button": None,
            "ecoDisplay": None,
            "vimeoUrl": None,
            "vimeoUrlMobile": None,
            "primaryHeaderVideo": None,
            "primaryHeaderVideoMobile": None,
            "headerVideo": None,
            "headerVideoMobile": None,
            "headerImage": None,
            "headerImageMobile": None,
        },
        "businessHours": {
            "isOpen": True,
            "openTime": "09:00:00",
            "closeTime": "18:00:00",
            "userFriendlyText": "09:00 tot 18:00",
        },
        "chanceOfRain": None,
    }


@pytest.fixture
def null_day_payload() -> dict:
    """A payload where suggestion is entirely null (day 6)."""
    return {
        "temperature": None,
        "iconUrl": None,
        "suggestion": None,
        "businessHours": {
            "isOpen": True,
            "openTime": "09:00:00",
            "closeTime": "18:00:00",
            "userFriendlyText": "09:00 tot 18:00",
        },
        "chanceOfRain": None,
    }


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None, None, None]:
    """Enable loading of the custom integration in all tests."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """A config entry for the integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Burgers Zoo",
        data={CONF_LANGUAGE: "nl", CONF_FORECAST_DAYS: 3},
        unique_id=SINGLE_INSTANCE_UNIQUE_ID,
    )


@pytest.fixture
def mock_api(full_day_payload: dict) -> Generator[aioresponses, None, None]:
    """Mock the Burgers Zoo API for days 0-2."""
    # Only the default nl-NL culture is registered; tests using other languages must register their own URLs.
    with aioresponses() as mocked:
        for day in range(3):
            mocked.get(
                f"https://www.burgerszoo.nl/api/weather/{day}?culture=nl-NL",
                payload=full_day_payload,
                repeat=True,
            )
        yield mocked
