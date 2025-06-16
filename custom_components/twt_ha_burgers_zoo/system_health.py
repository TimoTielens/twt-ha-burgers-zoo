from homeassistant.components import system_health
import logging

_LOGGER = logging.getLogger(__name__)

# Store last API status and error in hass.data
LAST_API_STATUS_KEY = "last_api_status"
LAST_API_ERROR_KEY = "last_api_error"

async def async_register_system_health(hass, domain, config):
    async def info_callback(hass):
        state = hass.states.get(f"sensor.{domain}_business_hours")
        business_hours = state.state if state else None
        last_status = hass.data.get(domain, {}).get(LAST_API_STATUS_KEY, "unknown")
        last_error = hass.data.get(domain, {}).get(LAST_API_ERROR_KEY)
        info = {
            "API reachable": last_status == "ok",
            "businessHours": business_hours,
        }
        if last_error:
            info["last_error"] = last_error
        return info

    system_health.register_callback(hass, domain, info_callback)
