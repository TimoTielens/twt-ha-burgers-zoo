"""Sensor platform for the Burgers Zoo integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BurgersZooConfigEntry
from .const import DOMAIN, NAME
from .coordinator import BurgersZooDataUpdateCoordinator
from .models import DayData

MANUFACTURER = "Burgers' Zoo"
CONFIGURATION_URL = "https://www.burgerszoo.nl"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BurgersZooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Burgers Zoo sensors from a config entry.

    One entity is created per configured forecast day. Iterating the configured
    day count (rather than the fetched data) keeps the entity set stable; an
    entity for a day the API did not return simply reports unavailable.
    """
    coordinator = entry.runtime_data
    entities: list[BurgersZooBaseEntity] = []
    for day in range(coordinator.forecast_days):
        entities.append(BurgersZooTemperatureSensor(coordinator, entry, day))
        entities.append(BurgersZooRainSensor(coordinator, entry, day))
    async_add_entities(entities)


class BurgersZooBaseEntity(
    CoordinatorEntity[BurgersZooDataUpdateCoordinator], SensorEntity
):
    """Base entity shared by all Burgers Zoo sensors.

    Groups every entity under one device, builds a stable unique id from the
    sensor key and forecast day, and reports unavailable when the coordinator
    has no data for that day.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BurgersZooDataUpdateCoordinator,
        entry: BurgersZooConfigEntry,
        day: int,
        key: str,
    ) -> None:
        """Initialise for a forecast day (0 = today) and a sensor-type key."""
        super().__init__(coordinator)
        self._day = day
        self._attr_unique_id = f"{entry.entry_id}_{key}_{day}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=CONFIGURATION_URL,
        )

    @property
    def _day_data(self) -> DayData | None:
        """Return this entity's day data, or None when it is unavailable."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._day)

    @property
    def available(self) -> bool:
        """Return True only when the coordinator has data for this day."""
        return super().available and self._day_data is not None


class BurgersZooTemperatureSensor(BurgersZooBaseEntity):
    """Expected temperature for a single forecast day."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BurgersZooDataUpdateCoordinator,
        entry: BurgersZooConfigEntry,
        day: int,
    ) -> None:
        """Initialise the temperature sensor for a forecast day."""
        super().__init__(coordinator, entry, day, key="temperature")
        self._attr_name = "Temperature" if day == 0 else f"Temperature day +{day}"

    @property
    def native_value(self) -> int | None:
        """Return the expected temperature in degrees Celsius."""
        data = self._day_data
        return data.temperature if data is not None else None


class BurgersZooRainSensor(BurgersZooBaseEntity):
    """Precipitation chance for a single forecast day."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BurgersZooDataUpdateCoordinator,
        entry: BurgersZooConfigEntry,
        day: int,
    ) -> None:
        """Initialise the chance-of-rain sensor for a forecast day."""
        super().__init__(coordinator, entry, day, key="chance_of_rain")
        self._attr_name = (
            "Chance of rain" if day == 0 else f"Chance of rain day +{day}"
        )

    @property
    def native_value(self) -> int | None:
        """Return the precipitation chance as a percentage."""
        data = self._day_data
        return data.chance_of_rain if data is not None else None
