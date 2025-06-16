import asyncio
import logging
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.entity import Entity
import aiohttp
from datetime import datetime, time
import pytz

DOMAIN = "twt_ha_burgers_zoo"
_LOGGER = logging.getLogger(__name__)

API_URL = "https://www.burgerszoo.nl/api/weather/0?culture=nl-NL"
LAST_API_STATUS_KEY = "last_api_status"
LAST_API_ERROR_KEY = "last_api_error"
AMSTERDAM_TZ = pytz.timezone("Europe/Amsterdam")

async def async_setup(hass: HomeAssistant, config: dict):
    business_hours_entity_id = f"sensor.{DOMAIN}_business_hours"
    weather_entity_id = f"sensor.{DOMAIN}_weather"

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    def get_state_from_hours(open_time_str, close_time_str):
        now = datetime.now(AMSTERDAM_TZ).time()
        try:
            open_time = datetime.strptime(open_time_str, "%H:%M:%S").time()
            close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()
            if open_time <= now < close_time:
                return "open"
            else:
                return "closed"
        except Exception as e:
            _LOGGER.error(f"Error parsing open/close time: {e}")
            return "unknown"

    async def set_business_hours_in_hass(business_hours):
        attrs = {}
        state = "unknown"
        if isinstance(business_hours, dict):
            attrs = {k: business_hours[k] for k in ("openTime", "closeTime", "userFriendlyText") if k in business_hours}
            if "openTime" in business_hours and "closeTime" in business_hours:
                state = get_state_from_hours(business_hours["openTime"], business_hours["closeTime"])
        hass.states.async_set(
            business_hours_entity_id,
            state,
            attributes=attrs
        )

    async def set_weather_in_hass(chance_of_rain, temperature, icon_url):
        attrs = {}
        state = "unknown"
        if temperature is not None:
            state = temperature
        if chance_of_rain is not None:
            attrs["chanceOfRain"] = chance_of_rain
        if temperature is not None:
            attrs["temperature"] = temperature
        if icon_url is not None:
            attrs["iconUrl"] = icon_url
        hass.states.async_set(
            weather_entity_id,
            state,
            attributes=attrs
        )

    async def call_external_api(_=None):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        business_hours = data.get("businessHours")
                        chance_of_rain = data.get("chanceOfRain")
                        temperature = data.get("temperature")
                        icon_url = data.get("iconUrl")

                        if business_hours is not None:
                            await set_business_hours_in_hass(business_hours)
                            _LOGGER.info(f"Set businessHours: {business_hours}")
                        else:
                            _LOGGER.warning("businessHours not found in API response.")

                        # Set weather sensor
                        await set_weather_in_hass(chance_of_rain, temperature, icon_url)
                        _LOGGER.info(f"Set weather: chanceOfRain={chance_of_rain}, temperature={temperature}, iconUrl={icon_url}")

                        hass.data[DOMAIN][LAST_API_STATUS_KEY] = "ok"
                        hass.data[DOMAIN][LAST_API_ERROR_KEY] = None
                    else:
                        _LOGGER.error(f"API call failed with status: {response.status}")
                        hass.data[DOMAIN][LAST_API_STATUS_KEY] = "fail"
                        hass.data[DOMAIN][LAST_API_ERROR_KEY] = f"Status: {response.status}"
            except Exception as e:
                _LOGGER.error(f"Error calling external API: {e}")
                hass.data[DOMAIN][LAST_API_STATUS_KEY] = "fail"
                hass.data[DOMAIN][LAST_API_ERROR_KEY] = str(e)

    # Call API after Home Assistant starts
    @callback
    def ha_started(event):
        hass.async_create_task(call_external_api())
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, ha_started)

    # Schedule API call at 01:00 every day
    async def schedule_api_call(now):
        await call_external_api()
    async_track_time_change(hass, schedule_api_call, hour=1, minute=0, second=0)

    return True
