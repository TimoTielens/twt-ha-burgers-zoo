"""Sensor platform for the Burgers Zoo integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BurgersZooConfigEntry
from .const import DOMAIN, NAME
from .coordinator import BurgersZooDataUpdateCoordinator

MANUFACTURER = "Burgers' Zoo"
CONFIGURATION_URL = "https://www.burgerszoo.nl"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BurgersZooConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Burgers Zoo sensors from a config entry.

    The coordinator is available via ``entry.runtime_data``. Concrete per-day
    sensors are added by follow-up features; this platform currently registers
    none.
    """


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
    def available(self) -> bool:
        """Return True only when the coordinator has data for this day."""
        return (
            super().available
            and self.coordinator.data is not None
            and self._day in self.coordinator.data
        )
