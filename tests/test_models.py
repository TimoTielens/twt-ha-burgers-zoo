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
