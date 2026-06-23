# Burgers Zoo Integration — Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the plumbing for a HACS-installable Home Assistant integration that retrieves Burgers' Zoo data — typed async API client, data coordinator, config + options flow, and a full test/CI harness. No entities yet.

**Architecture:** A single `DataUpdateCoordinator` fetches all configured days (indices `0..N-1`) in one refresh via `asyncio.gather` and stores `{day_index: DayData}`. A typed async API client wraps Home Assistant's shared aiohttp session and normalizes errors into two exceptions. A UI config flow (plus options flow) collects `language` and `forecast_days`. The integration creates zero entities — sensors are added later, feature by feature.

**Tech Stack:** Python 3.13, Home Assistant custom component, aiohttp (HA-bundled), voluptuous, pytest + pytest-homeassistant-custom-component + aioresponses, GitHub Actions (hassfest + HACS validation).

## Global Constraints

- Integration domain: `twt_ha_burgers_zoo` (verbatim, matches the folder name).
- API endpoint: `https://www.burgerszoo.nl/api/weather/{day}?culture={culture}` — no auth, no secrets.
- Valid day indices: `0`–`4` only (days 5+ return HTTP 200 with all-null payloads). `forecast_days` range is `1`–`5`, default `3`.
- Cultures: `nl→nl-NL`, `en→en-US`, `de→de-DE`. Default language `nl`.
- `manifest.json`: `config_flow: true`, `iot_class: "cloud_polling"`, `integration_type: "service"`, `requirements: []`.
- Single config entry only.
- Coordinator update interval fixed at 1 hour (not user-configurable).
- The base parses but never interprets: no placeholder substitution, no HTML stripping, no open/closed logic, no media-URL absolutization. Raw values preserved.
- Defensive parsing: every field via `.get()`; missing/null nested objects → `None`; never raise on a partial or all-null payload.
- TDD throughout. Commit after every green task.

---

## File Structure

```
custom_components/twt_ha_burgers_zoo/
├── __init__.py          # async_setup_entry / async_unload_entry / async_reload_entry
├── api.py               # BurgersZooApiClient + exceptions
├── coordinator.py       # BurgersZooDataUpdateCoordinator
├── config_flow.py       # config flow (user step) + options flow
├── const.py             # DOMAIN, conf keys, defaults, culture map, URLs
├── models.py            # BusinessHours, Suggestion, DayData dataclasses + from_json
├── manifest.json
├── strings.json
└── translations/
    ├── en.json
    └── nl.json
tests/
├── __init__.py
├── conftest.py          # pytest plugin wiring + payload fixtures + HA fixtures
├── test_models.py
├── test_api.py
├── test_coordinator.py
├── test_init.py
└── test_config_flow.py
hacs.json
pyproject.toml           # pytest config
requirements_test.txt
.github/workflows/validate.yml
.github/workflows/test.yml
```

---

## Task 1: Test tooling, constants, and models

**Files:**
- Create: `requirements_test.txt`
- Create: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `custom_components/twt_ha_burgers_zoo/__init__.py` (empty placeholder for now)
- Create: `custom_components/twt_ha_burgers_zoo/const.py`
- Create: `custom_components/twt_ha_burgers_zoo/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `const.py` symbols — `DOMAIN`, `NAME`, `SINGLE_INSTANCE_UNIQUE_ID`, `CONF_LANGUAGE`, `CONF_FORECAST_DAYS`, `DEFAULT_LANGUAGE`, `DEFAULT_FORECAST_DAYS`, `MIN_FORECAST_DAYS`, `MAX_FORECAST_DAYS`, `LANGUAGES`, `CULTURE_MAP`, `API_URL_TEMPLATE`, `API_TIMEOUT`, `UPDATE_INTERVAL_HOURS`.
- Produces: `models.py` — `BusinessHours`, `Suggestion`, `DayData` frozen dataclasses, each with `@classmethod from_json(cls, data: dict | None)` returning an instance (or `None` when `data` is falsy for the nested ones). `DayData.from_json(data: dict)` always returns a `DayData`.
- Produces: `tests/conftest.py` fixtures — `full_day_payload`, `empty_suggestion_payload`, `null_day_payload` (dicts).

- [ ] **Step 1: Create test dependencies file**

Create `requirements_test.txt`:

```
pytest-homeassistant-custom-component
aioresponses
```

- [ ] **Step 2: Create pytest config**

Create `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Install test dependencies**

Run: `pip install -r requirements_test.txt`
Expected: installs `homeassistant`, `pytest`, `pytest-homeassistant-custom-component`, `aioresponses` and dependencies.

- [ ] **Step 4: Create constants**

Create `custom_components/twt_ha_burgers_zoo/const.py`:

```python
"""Constants for the Burgers Zoo integration."""
from __future__ import annotations

DOMAIN = "twt_ha_burgers_zoo"
NAME = "Burgers Zoo"
SINGLE_INSTANCE_UNIQUE_ID = "burgers_zoo"

CONF_LANGUAGE = "language"
CONF_FORECAST_DAYS = "forecast_days"

DEFAULT_LANGUAGE = "nl"
DEFAULT_FORECAST_DAYS = 3
MIN_FORECAST_DAYS = 1
MAX_FORECAST_DAYS = 5

LANGUAGES = ["nl", "en", "de"]
CULTURE_MAP = {"nl": "nl-NL", "en": "en-US", "de": "de-DE"}

API_URL_TEMPLATE = "https://www.burgerszoo.nl/api/weather/{day}?culture={culture}"
API_TIMEOUT = 10
UPDATE_INTERVAL_HOURS = 1
```

- [ ] **Step 5: Create empty package init (placeholder)**

Create `custom_components/twt_ha_burgers_zoo/__init__.py`:

```python
"""The Burgers Zoo integration."""
```

- [ ] **Step 6: Create tests package and conftest with payload fixtures**

Create `tests/__init__.py`:

```python
"""Tests for the Burgers Zoo integration."""
```

Create `tests/conftest.py`:

```python
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
```

- [ ] **Step 7: Write the failing models test**

Create `tests/test_models.py`:

```python
"""Tests for Burgers Zoo data models."""
from __future__ import annotations

from custom_components.twt_ha_burgers_zoo.models import (
    BusinessHours,
    DayData,
    Suggestion,
)


def test_day_data_parses_full_payload(full_day_payload: dict) -> None:
    day = DayData.from_json(full_day_payload)

    assert day.temperature == 30
    assert day.chance_of_rain == 10
    assert day.icon_url == "FullSun"

    assert isinstance(day.business_hours, BusinessHours)
    assert day.business_hours.is_open is True
    assert day.business_hours.open_time == "09:00:00"
    assert day.business_hours.close_time == "18:00:00"
    assert day.business_hours.user_friendly_text == "09:00 tot 18:00"

    assert isinstance(day.suggestion, Suggestion)
    assert day.suggestion.eco_display == "safari"
    assert day.suggestion.title == "Ontdek de Oost-Afrikaanse savanne!"
    assert day.suggestion.slogan == "In één dag op wereldreis!"
    assert day.suggestion.block_title == "Tip! Ga op safari op onze savannevlakte"
    assert day.suggestion.content.startswith("<p>{{dayText}}")
    assert day.suggestion.button_name == "Bezoek de savannevlakte"
    assert day.suggestion.button_url == "https://www.burgerszoo.nl/reserveren"
    assert day.suggestion.button_target is None
    assert day.suggestion.header_video == "/media/jcadvkml/safari-1-2-small.mp4"
    assert day.suggestion.header_video_mobile == "/media/mjojmyus/safari-1-2-small.mp4"
    assert day.suggestion.header_image == "/media/djnj14z5/safari-still.jpg?width=1920"
    assert day.suggestion.header_image_mobile is None
    assert day.suggestion.vimeo_url == ""


def test_day_data_parses_empty_suggestion(empty_suggestion_payload: dict) -> None:
    day = DayData.from_json(empty_suggestion_payload)

    assert day.temperature is None
    assert day.chance_of_rain is None
    assert day.icon_url is None
    # suggestion object present but all fields null
    assert isinstance(day.suggestion, Suggestion)
    assert day.suggestion.title is None
    assert day.suggestion.content is None
    assert day.suggestion.button_name is None
    # business hours still present
    assert day.business_hours.is_open is True


def test_day_data_parses_null_suggestion(null_day_payload: dict) -> None:
    day = DayData.from_json(null_day_payload)

    assert day.suggestion is None
    assert day.business_hours is not None
    assert day.temperature is None


def test_day_data_handles_missing_keys() -> None:
    day = DayData.from_json({})

    assert day.temperature is None
    assert day.chance_of_rain is None
    assert day.icon_url is None
    assert day.business_hours is None
    assert day.suggestion is None
```

- [ ] **Step 8: Run the test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.twt_ha_burgers_zoo.models'`

- [ ] **Step 9: Implement the models**

Create `custom_components/twt_ha_burgers_zoo/models.py`:

```python
"""Data models for the Burgers Zoo integration."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessHours:
    """Opening hours for a single day."""

    is_open: bool
    open_time: str | None
    close_time: str | None
    user_friendly_text: str | None

    @classmethod
    def from_json(cls, data: dict | None) -> "BusinessHours | None":
        if not data:
            return None
        return cls(
            is_open=bool(data.get("isOpen")),
            open_time=data.get("openTime"),
            close_time=data.get("closeTime"),
            user_friendly_text=data.get("userFriendlyText"),
        )


@dataclass(frozen=True)
class Suggestion:
    """Eco-display suggestion for a single day. Raw values, untouched."""

    eco_display: str | None
    title: str | None
    slogan: str | None
    block_title: str | None
    content: str | None
    button_name: str | None
    button_url: str | None
    button_target: str | None
    vimeo_url: str | None
    vimeo_url_mobile: str | None
    primary_header_video: str | None
    primary_header_video_mobile: str | None
    header_video: str | None
    header_video_mobile: str | None
    header_image: str | None
    header_image_mobile: str | None

    @classmethod
    def from_json(cls, data: dict | None) -> "Suggestion | None":
        if not data:
            return None
        button = data.get("button") or {}
        return cls(
            eco_display=data.get("ecoDisplay"),
            title=data.get("ecoDisplayTitle"),
            slogan=data.get("ecoDisplaySlogan"),
            block_title=data.get("ecoDisplayBlockTitle"),
            content=data.get("content"),
            button_name=button.get("name"),
            button_url=button.get("url"),
            button_target=button.get("target"),
            vimeo_url=data.get("vimeoUrl"),
            vimeo_url_mobile=data.get("vimeoUrlMobile"),
            primary_header_video=data.get("primaryHeaderVideo"),
            primary_header_video_mobile=data.get("primaryHeaderVideoMobile"),
            header_video=data.get("headerVideo"),
            header_video_mobile=data.get("headerVideoMobile"),
            header_image=data.get("headerImage"),
            header_image_mobile=data.get("headerImageMobile"),
        )


@dataclass(frozen=True)
class DayData:
    """All data for a single forecast day."""

    temperature: int | None
    chance_of_rain: int | None
    icon_url: str | None
    business_hours: BusinessHours | None
    suggestion: Suggestion | None

    @classmethod
    def from_json(cls, data: dict) -> "DayData":
        return cls(
            temperature=data.get("temperature"),
            chance_of_rain=data.get("chanceOfRain"),
            icon_url=data.get("iconUrl"),
            business_hours=BusinessHours.from_json(data.get("businessHours")),
            suggestion=Suggestion.from_json(data.get("suggestion")),
        )
```

- [ ] **Step 10: Run the test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (4 passed)

- [ ] **Step 11: Commit**

```bash
git add requirements_test.txt pyproject.toml tests/__init__.py tests/conftest.py custom_components/twt_ha_burgers_zoo/__init__.py custom_components/twt_ha_burgers_zoo/const.py custom_components/twt_ha_burgers_zoo/models.py tests/test_models.py
git commit -m "Add constants, data models, and test tooling"
```

---

## Task 2: API client and exceptions

**Files:**
- Create: `custom_components/twt_ha_burgers_zoo/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `const.py` (`API_URL_TEMPLATE`, `API_TIMEOUT`, `CULTURE_MAP`); `models.DayData`.
- Produces: exceptions `BurgersZooError` (base), `BurgersZooConnectionError`, `BurgersZooApiError`.
- Produces: `class BurgersZooApiClient` with `__init__(self, session: aiohttp.ClientSession, language: str)`, `async def async_get_day(self, day: int) -> DayData`, `async def async_get_days(self, count: int) -> dict[int, DayData]`.

- [ ] **Step 1: Write the failing API client tests**

Create `tests/test_api.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.twt_ha_burgers_zoo.api'`

- [ ] **Step 3: Implement the API client**

Create `custom_components/twt_ha_burgers_zoo/api.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add custom_components/twt_ha_burgers_zoo/api.py tests/test_api.py
git commit -m "Add Burgers Zoo API client with error handling"
```

---

## Task 3: Data update coordinator

**Files:**
- Create: `custom_components/twt_ha_burgers_zoo/coordinator.py`
- Test: `tests/test_coordinator.py`

**Interfaces:**
- Consumes: `const.py` (`DOMAIN`, `UPDATE_INTERVAL_HOURS`); `api` (`BurgersZooApiClient`, `BurgersZooError`); `models.DayData`.
- Produces: `class BurgersZooDataUpdateCoordinator(DataUpdateCoordinator[dict[int, DayData]])` with `__init__(self, hass, client: BurgersZooApiClient, forecast_days: int)` and `async def _async_update_data(self) -> dict[int, DayData]`. Public attributes: `self.client`, `self.forecast_days`.

- [ ] **Step 1: Write the failing coordinator tests**

Create `tests/test_coordinator.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_coordinator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.twt_ha_burgers_zoo.coordinator'`

- [ ] **Step 3: Implement the coordinator**

Create `custom_components/twt_ha_burgers_zoo/coordinator.py`:

```python
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
        try:
            return await self.client.async_get_days(self.forecast_days)
        except BurgersZooError as err:
            raise UpdateFailed(str(err)) from err
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_coordinator.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add custom_components/twt_ha_burgers_zoo/coordinator.py tests/test_coordinator.py
git commit -m "Add data update coordinator"
```

---

## Task 4: Integration bootstrap — manifest, setup/unload, config flow

**Files:**
- Create: `custom_components/twt_ha_burgers_zoo/manifest.json`
- Create: `custom_components/twt_ha_burgers_zoo/strings.json`
- Create: `custom_components/twt_ha_burgers_zoo/translations/en.json`
- Create: `custom_components/twt_ha_burgers_zoo/translations/nl.json`
- Modify: `custom_components/twt_ha_burgers_zoo/__init__.py` (replace placeholder)
- Create: `custom_components/twt_ha_burgers_zoo/config_flow.py`
- Modify: `tests/conftest.py` (add HA fixtures)
- Test: `tests/test_init.py`
- Test: `tests/test_config_flow.py`

**Interfaces:**
- Consumes: `const.py`, `api`, `coordinator`.
- Produces: `__init__.py` — `BurgersZooConfigEntry` type alias, `PLATFORMS: list[Platform] = []`, `async_setup_entry`, `async_unload_entry`, `async_reload_entry`. After setup, `entry.runtime_data` holds the coordinator.
- Produces: `config_flow.py` — `class BurgersZooConfigFlow(ConfigFlow, domain=DOMAIN)` with `async_step_user`. Config-entry data keys: `CONF_LANGUAGE`, `CONF_FORECAST_DAYS` (int).
- Produces in `conftest.py`: autouse `auto_enable_custom_integrations` fixture; `mock_config_entry` fixture (a `MockConfigEntry` with `domain=DOMAIN`, `data={CONF_LANGUAGE: "nl", CONF_FORECAST_DAYS: 3}`, `unique_id=SINGLE_INSTANCE_UNIQUE_ID`); `mock_api` fixture (an `aioresponses` context registering days 0–2 with a valid payload).

- [ ] **Step 1: Create the manifest**

Create `custom_components/twt_ha_burgers_zoo/manifest.json`:

```json
{
  "domain": "twt_ha_burgers_zoo",
  "name": "Burgers Zoo",
  "version": "0.1.0",
  "codeowners": ["@TimoTielens"],
  "config_flow": true,
  "documentation": "https://github.com/TimoTielens/twt-ha-burgers-zoo",
  "integration_type": "service",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/TimoTielens/twt-ha-burgers-zoo/issues",
  "requirements": []
}
```

- [ ] **Step 2: Create UI strings and translations**

Create `custom_components/twt_ha_burgers_zoo/strings.json`:

```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "language": "Language",
          "forecast_days": "Number of forecast days"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to the Burgers Zoo API."
    },
    "abort": {
      "single_instance_allowed": "Only a single Burgers Zoo instance is allowed.",
      "already_configured": "Burgers Zoo is already configured."
    }
  },
  "options": {
    "step": {
      "init": {
        "data": {
          "language": "Language",
          "forecast_days": "Number of forecast days"
        }
      }
    }
  },
  "selector": {
    "language": {
      "options": {
        "nl": "Nederlands",
        "en": "English",
        "de": "Deutsch"
      }
    }
  }
}
```

Create `custom_components/twt_ha_burgers_zoo/translations/en.json` with identical content to `strings.json` above.

Create `custom_components/twt_ha_burgers_zoo/translations/nl.json`:

```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "language": "Taal",
          "forecast_days": "Aantal voorspelde dagen"
        }
      }
    },
    "error": {
      "cannot_connect": "Verbinden met de Burgers Zoo API is mislukt."
    },
    "abort": {
      "single_instance_allowed": "Er is slechts één Burgers Zoo-instantie toegestaan.",
      "already_configured": "Burgers Zoo is al geconfigureerd."
    }
  },
  "options": {
    "step": {
      "init": {
        "data": {
          "language": "Taal",
          "forecast_days": "Aantal voorspelde dagen"
        }
      }
    }
  },
  "selector": {
    "language": {
      "options": {
        "nl": "Nederlands",
        "en": "English",
        "de": "Deutsch"
      }
    }
  }
}
```

- [ ] **Step 3: Implement `__init__.py` (setup/unload/reload)**

Replace `custom_components/twt_ha_burgers_zoo/__init__.py`:

```python
"""The Burgers Zoo integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BurgersZooApiClient
from .const import CONF_FORECAST_DAYS, CONF_LANGUAGE
from .coordinator import BurgersZooDataUpdateCoordinator

PLATFORMS: list[Platform] = []

BurgersZooConfigEntry = ConfigEntry[BurgersZooDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: BurgersZooConfigEntry
) -> bool:
    """Set up Burgers Zoo from a config entry."""
    language = entry.options.get(
        CONF_LANGUAGE, entry.data[CONF_LANGUAGE]
    )
    forecast_days = entry.options.get(
        CONF_FORECAST_DAYS, entry.data[CONF_FORECAST_DAYS]
    )

    session = async_get_clientsession(hass)
    client = BurgersZooApiClient(session, language)
    coordinator = BurgersZooDataUpdateCoordinator(hass, client, forecast_days)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BurgersZooConfigEntry
) -> bool:
    """Unload a Burgers Zoo config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant, entry: BurgersZooConfigEntry
) -> None:
    """Reload the config entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
```

- [ ] **Step 4: Implement the config flow (user step only)**

Create `custom_components/twt_ha_burgers_zoo/config_flow.py`:

```python
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
```

- [ ] **Step 5: Add HA fixtures to conftest**

Add to `tests/conftest.py` (append after the existing fixtures):

```python
from collections.abc import Generator

from aioresponses import aioresponses
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.twt_ha_burgers_zoo.const import (
    CONF_FORECAST_DAYS,
    CONF_LANGUAGE,
    DOMAIN,
    SINGLE_INSTANCE_UNIQUE_ID,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
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
    with aioresponses() as mocked:
        for day in range(3):
            mocked.get(
                f"https://www.burgerszoo.nl/api/weather/{day}?culture=nl-NL",
                payload=full_day_payload,
                repeat=True,
            )
        yield mocked
```

Note: move the three `import` lines and `from` lines to the top of the file with the existing imports if preferred; functionally they may sit inline. Keep `pytest_plugins` at module top level.

- [ ] **Step 6: Write the failing init lifecycle test**

Create `tests/test_init.py`:

```python
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
```

- [ ] **Step 7: Write the failing config-flow test**

Create `tests/test_config_flow.py`:

```python
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
```

- [ ] **Step 8: Run the new tests to verify they fail**

Run: `pytest tests/test_init.py tests/test_config_flow.py -v`
Expected: FAIL — config flow / setup not yet wired (e.g. `Unknown flow` or import errors) before the implementation steps above are saved. (If you implemented steps 1–4 first, they should now PASS; the strict TDD order is to confirm a red state before code — if already green, proceed.)

- [ ] **Step 9: Run the tests to verify they pass**

Run: `pytest tests/test_init.py tests/test_config_flow.py -v`
Expected: PASS (test_init: 2 passed, test_config_flow: 3 passed)

- [ ] **Step 10: Run the full suite**

Run: `pytest -v`
Expected: PASS (all tests from Tasks 1–4 green)

- [ ] **Step 11: Commit**

```bash
git add custom_components/twt_ha_burgers_zoo/manifest.json custom_components/twt_ha_burgers_zoo/strings.json custom_components/twt_ha_burgers_zoo/translations custom_components/twt_ha_burgers_zoo/__init__.py custom_components/twt_ha_burgers_zoo/config_flow.py tests/conftest.py tests/test_init.py tests/test_config_flow.py
git commit -m "Wire up integration setup, unload, and config flow"
```

---

## Task 5: Options flow (reconfiguration + reload)

**Files:**
- Modify: `custom_components/twt_ha_burgers_zoo/config_flow.py`
- Test: `tests/test_config_flow.py` (add options-flow tests)

**Interfaces:**
- Consumes: `build_schema` from Task 4; `BurgersZooConfigFlow`.
- Produces: `BurgersZooConfigFlow.async_get_options_flow` (static) returning `BurgersZooOptionsFlow`; `class BurgersZooOptionsFlow(OptionsFlow)` with `async_step_init`. Saving options stores `{CONF_LANGUAGE, CONF_FORECAST_DAYS(int)}` in `entry.options` and triggers a reload (via the update listener registered in `async_setup_entry`).

- [ ] **Step 1: Write the failing options-flow test**

Add to `tests/test_config_flow.py`:

```python
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
```

Note: `mock_api` registers `nl-NL` days 0–2 with `repeat=True`; the post-options reload requests `en-US` days 0–4. Extend the `mock_api` fixture in `tests/conftest.py` to also register all five days for every culture so the reload succeeds. Replace the `mock_api` fixture body with:

```python
@pytest.fixture
def mock_api(full_day_payload: dict) -> Generator[aioresponses, None, None]:
    """Mock the Burgers Zoo API for all days and cultures."""
    with aioresponses() as mocked:
        for culture in ("nl-NL", "en-US", "de-DE"):
            for day in range(5):
                mocked.get(
                    f"https://www.burgerszoo.nl/api/weather/{day}?culture={culture}",
                    payload=full_day_payload,
                    repeat=True,
                )
        yield mocked
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_config_flow.py::test_options_flow_updates_entry -v`
Expected: FAIL — no options flow handler registered (`Handler does not support options flow` or similar).

- [ ] **Step 3: Implement the options flow**

Add to `custom_components/twt_ha_burgers_zoo/config_flow.py`. Update the imports line to include `OptionsFlow` and `callback`:

```python
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
```

Add the static method inside `BurgersZooConfigFlow`:

```python
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "BurgersZooOptionsFlow":
        return BurgersZooOptionsFlow()
```

Append the options flow class at the end of the file:

```python
class BurgersZooOptionsFlow(OptionsFlow):
    """Handle Burgers Zoo options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            user_input[CONF_FORECAST_DAYS] = int(user_input[CONF_FORECAST_DAYS])
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=build_schema(current),
        )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_config_flow.py::test_options_flow_updates_entry -v`
Expected: PASS

- [ ] **Step 5: Run the full suite**

Run: `pytest -v`
Expected: PASS (all green)

- [ ] **Step 6: Commit**

```bash
git add custom_components/twt_ha_burgers_zoo/config_flow.py tests/conftest.py tests/test_config_flow.py
git commit -m "Add options flow with reload on change"
```

---

## Task 6: Packaging and CI

**Files:**
- Create: `hacs.json`
- Create: `.github/workflows/validate.yml`
- Create: `.github/workflows/test.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing (packaging only).
- Produces: HACS-installable repo + CI that runs hassfest, HACS validation, and pytest.

- [ ] **Step 1: Create HACS metadata**

Create `hacs.json`:

```json
{
  "name": "Burgers Zoo",
  "render_readme": true,
  "homeassistant": "2024.12.0"
}
```

- [ ] **Step 2: Create the validation workflow**

Create `.github/workflows/validate.yml`:

```yaml
name: Validate

on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"

jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
```

- [ ] **Step 3: Create the test workflow**

Create `.github/workflows/test.yml`:

```yaml
name: Test

on:
  push:
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: pip install -r requirements_test.txt
      - name: Run tests
        run: pytest
```

- [ ] **Step 4: Update the README**

Replace `README.md`:

```markdown
# twt-ha-burgers-zoo

A HACS-installable Home Assistant integration that retrieves data from the
Dutch zoo in Arnhem, Burgers' Zoo — opening hours, expected temperature, and
the daily eco-display suggestion, for today and several days ahead.

## Status

Base / plumbing only. The API client, data coordinator, and config flow are in
place; sensor entities are added in subsequent releases.

## Installation (HACS)

1. Add this repository as a custom repository in HACS (category: Integration).
2. Install "Burgers Zoo".
3. Restart Home Assistant.
4. Add the integration via **Settings → Devices & Services → Add Integration → Burgers Zoo**.

## Configuration

- **Language** — `nl`, `en`, or `de` (default `nl`).
- **Forecast days** — 1–5 (default 3).

Both can be changed later via the integration's options.

## Development

```bash
pip install -r requirements_test.txt
pytest
```
```

- [ ] **Step 5: Run the full suite one final time**

Run: `pytest -v`
Expected: PASS (all tests green)

- [ ] **Step 6: Commit**

```bash
git add hacs.json .github/workflows/validate.yml .github/workflows/test.yml README.md
git commit -m "Add HACS metadata, CI workflows, and README"
```

---

## Self-Review Notes

- **Spec coverage:** API client (Task 2) ✓; models incl. media fields (Task 1) ✓; coordinator + fixed 1h interval (Task 3) ✓; config flow with language + forecast_days 1–5 (Task 4) ✓; options flow + reload (Task 5) ✓; manifest fixes — cloud_polling/service/config_flow (Task 4) ✓; single instance (Task 4) ✓; error mapping → UpdateFailed/cannot_connect (Tasks 2–4) ✓; full test harness + aioresponses (all tasks) ✓; CI hassfest/HACS + hacs.json (Task 6) ✓; no entities created ✓.
- **Out of scope confirmed absent:** no `sensor.py`, no placeholder substitution, no HTML stripping, no open/closed logic, no media-URL absolutization, no system_health.
- **Type consistency:** `BurgersZooApiClient(session, language)`, `async_get_day(day)`, `async_get_days(count) -> dict[int, DayData]`, `BurgersZooDataUpdateCoordinator(hass, client, forecast_days)`, `build_schema(defaults)` used consistently across tasks.
```
