"""Shared fixtures for Burgers Zoo tests."""
from __future__ import annotations

import pytest

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
