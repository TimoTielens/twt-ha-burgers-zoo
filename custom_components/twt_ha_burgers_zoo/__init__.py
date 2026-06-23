"""The Burgers Zoo integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BurgersZooApiClient
from .const import CONF_FORECAST_DAYS, CONF_LANGUAGE
from .coordinator import BurgersZooDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

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
