import asyncio
import logging
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.entity import Entity
import aiohttp
from datetime import datetime, time
import pytz
import locale

DOMAIN = "twt_ha_burgers_zoo"
_LOGGER = logging.getLogger(__name__)

API_URL_TEMPLATE = "https://www.burgerszoo.nl/api/weather/{}?culture=nl-NL"
LAST_API_STATUS_KEY = "last_api_status"
LAST_API_ERROR_KEY = "last_api_error"
AMSTERDAM_TZ = pytz.timezone("Europe/Amsterdam")

async def async_setup(hass: HomeAssistant, config: dict):
    business_hours_entity_ids = [f"sensor.{DOMAIN}_business_hours_{i}" for i in range(5)]
    weather_entity_ids = [f"sensor.{DOMAIN}_weather_{i}" for i in range(5)]
    suggestion_entity_ids = [f"sensor.{DOMAIN}_suggestion_{i}" for i in range(5)]

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    def get_state_from_hours(open_time_str, close_time_str, day_idx):
        now = datetime.now(AMSTERDAM_TZ)
        # For today, use current time; for future days, always 'closed' except if you want to calculate for that day
        if day_idx == 0:
            now_time = now.time()
            try:
                open_time = datetime.strptime(open_time_str, "%H:%M:%S").time()
                close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()
                if open_time <= now_time < close_time:
                    return "open"
                else:
                    return "closed"
            except Exception as e:
                _LOGGER.error(f"Error parsing open/close time: {e}")
                return "unknown"
        else:
            # For future days, just return 'closed' or 'open' based on your business logic
            return "closed"

    async def set_business_hours_in_hass(idx, business_hours):
        entity_id = business_hours_entity_ids[idx]
        attrs = {}
        state = "unknown"
        if isinstance(business_hours, dict):
            attrs = {k: business_hours[k] for k in ("openTime", "closeTime", "userFriendlyText") if k in business_hours}
            if "openTime" in business_hours and "closeTime" in business_hours:
                state = get_state_from_hours(business_hours["openTime"], business_hours["closeTime"], idx)
        hass.states.async_set(
            entity_id,
            state,
            attributes=attrs
        )

    async def set_weather_in_hass(idx, chance_of_rain, temperature, icon_url):
        entity_id = weather_entity_ids[idx]
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
            entity_id,
            state,
            attributes=attrs
        )

    # Dutch day names mapping
    DUTCH_DAYS = {
        'Monday': 'Maandag',
        'Tuesday': 'Dinsdag',
        'Wednesday': 'Woensdag',
        'Thursday': 'Donderdag',
        'Friday': 'Vrijdag',
        'Saturday': 'Zaterdag',
        'Sunday': 'Zondag',
    }

    async def set_suggestion_in_hass(idx, suggestion, temperature):
        entity_id = suggestion_entity_ids[idx]
        attrs = {}
        state = ""
        if isinstance(suggestion, dict):
            content = suggestion.get("content", "")
            # Replace {{temperatureText}} with the temperature value from the API
            if temperature is not None:
                content = content.replace("{{temperatureText}}", str(temperature))
            if idx == 0:
                day_text = "Vandaag"
            else:
                from datetime import datetime, timedelta
                day_en = (datetime.now(AMSTERDAM_TZ) + timedelta(days=idx)).strftime('%A')
                day_text = DUTCH_DAYS.get(day_en, day_en)
            content = content.replace("{{dayText}}", day_text)
            content = content.replace("\u003Cp\u003E", "").replace("\u003C/p\u003E", "")
            state = content
            for k in ("ecoDisplayTitle", "ecoDisplaySlogan", "ecoDisplayBlockTitle"):
                if k in suggestion:
                    attrs[k] = suggestion[k]
        hass.states.async_set(
            entity_id,
            state,
            attributes=attrs
        )

    async def call_external_api(_=None):
        async with aiohttp.ClientSession() as session:
            try:
                for i in range(5):
                    api_url = API_URL_TEMPLATE.format(i)
                    async with session.get(api_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            business_hours = data.get("businessHours")
                            chance_of_rain = data.get("chanceOfRain")
                            temperature = data.get("temperature")
                            icon_url = data.get("iconUrl")
                            suggestion = data.get("suggestion")
                            if business_hours is not None:
                                await set_business_hours_in_hass(i, business_hours)
                                _LOGGER.info(f"Set businessHours {i}: {business_hours}")
                            else:
                                _LOGGER.warning(f"businessHours not found in API response for day {i}.")
                            await set_weather_in_hass(i, chance_of_rain, temperature, icon_url)
                            _LOGGER.info(f"Set weather {i}: chanceOfRain={chance_of_rain}, temperature={temperature}, iconUrl={icon_url}")
                            if suggestion is not None:
                                await set_suggestion_in_hass(i, suggestion, temperature)
                                _LOGGER.info(f"Set suggestion {i}: {suggestion}")
                            else:
                                _LOGGER.warning(f"suggestion not found in API response for day {i}.")
                        else:
                            _LOGGER.error(f"API call failed for day {i} with status: {response.status}")
                            hass.data[DOMAIN][LAST_API_STATUS_KEY] = "fail"
                            hass.data[DOMAIN][LAST_API_ERROR_KEY] = f"Status: {response.status}"
                hass.data[DOMAIN][LAST_API_STATUS_KEY] = "ok"
                hass.data[DOMAIN][LAST_API_ERROR_KEY] = None
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
