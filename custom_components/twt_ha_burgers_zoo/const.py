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
