"""Tests for the Burgers Zoo sensor platform foundation."""
from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
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
from custom_components.twt_ha_burgers_zoo.sensor import (
    BurgersZooBaseEntity,
    BurgersZooTemperatureSensor,
)


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


async def test_temperature_sensor_reports_day_value(hass: HomeAssistant) -> None:
    entry = _entry()
    coordinator = _make_coordinator(hass, {0: DayData.from_json({"temperature": 30})})

    sensor = BurgersZooTemperatureSensor(coordinator, entry, day=0)

    assert sensor.native_value == 30
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.unique_id == f"{entry.entry_id}_temperature_0"


async def test_temperature_sensor_unknown_when_day_missing(
    hass: HomeAssistant,
) -> None:
    entry = _entry()
    coordinator = _make_coordinator(hass, {0: DayData.from_json({"temperature": 30})})

    sensor = BurgersZooTemperatureSensor(coordinator, entry, day=2)

    assert sensor.native_value is None
    assert sensor.available is False


async def test_temperature_sensor_per_forecast_day(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api,
) -> None:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        ent_reg, mock_config_entry.entry_id
    )
    temperature = [e for e in entities if "_temperature_" in e.unique_id]
    # mock_config_entry is configured with forecast_days = 3
    assert len(temperature) == 3

    today = next(e for e in temperature if e.unique_id.endswith("_temperature_0"))
    state = hass.states.get(today.entity_id)
    assert state is not None
    assert state.state == "30"
    assert state.attributes["device_class"] == "temperature"
    assert state.attributes["unit_of_measurement"] == "°C"
