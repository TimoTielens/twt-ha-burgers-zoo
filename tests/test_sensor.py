"""Tests for the Burgers Zoo sensor platform foundation."""
from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.twt_ha_burgers_zoo import PLATFORMS
from custom_components.twt_ha_burgers_zoo.const import (
    CONF_FORECAST_DAYS,
    CONF_LANGUAGE,
    DOMAIN,
    NAME,
    SINGLE_INSTANCE_UNIQUE_ID,
)
from custom_components.twt_ha_burgers_zoo.coordinator import (
    BurgersZooDataUpdateCoordinator,
)
from custom_components.twt_ha_burgers_zoo.models import DayData
from custom_components.twt_ha_burgers_zoo.sensor import BurgersZooBaseEntity


class _ProbeEntity(BurgersZooBaseEntity):
    """Minimal concrete subclass to exercise the abstract base."""


def _make_coordinator(
    hass: HomeAssistant, data: dict[int, DayData]
) -> BurgersZooDataUpdateCoordinator:
    coordinator = BurgersZooDataUpdateCoordinator(
        hass, AsyncMock(), forecast_days=len(data) or 1
    )
    coordinator.data = data
    return coordinator


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_LANGUAGE: "nl", CONF_FORECAST_DAYS: 1},
        unique_id=SINGLE_INSTANCE_UNIQUE_ID,
    )


def test_sensor_platform_registered() -> None:
    assert Platform.SENSOR in PLATFORMS


async def test_base_entity_device_info_groups_under_one_device(
    hass: HomeAssistant,
) -> None:
    entry = _entry()
    coordinator = _make_coordinator(hass, {0: DayData.from_json({"temperature": 30})})

    entity = _ProbeEntity(coordinator, entry, day=0, key="probe")

    info = entity.device_info
    assert info["identifiers"] == {(DOMAIN, entry.entry_id)}
    assert info["name"] == NAME
    assert info["manufacturer"] == "Burgers' Zoo"
    assert info["entry_type"] == DeviceEntryType.SERVICE


async def test_base_entity_unique_id_and_has_entity_name(
    hass: HomeAssistant,
) -> None:
    entry = _entry()
    coordinator = _make_coordinator(hass, {0: DayData.from_json({"temperature": 30})})

    entity = _ProbeEntity(coordinator, entry, day=2, key="probe")

    assert entity.unique_id == f"{entry.entry_id}_probe_2"
    assert entity.has_entity_name is True


async def test_base_entity_unavailable_when_day_missing(
    hass: HomeAssistant,
) -> None:
    entry = _entry()
    coordinator = _make_coordinator(hass, {0: DayData.from_json({"temperature": 30})})

    present = _ProbeEntity(coordinator, entry, day=0, key="probe")
    missing = _ProbeEntity(coordinator, entry, day=3, key="probe")

    assert present.available is True
    assert missing.available is False
