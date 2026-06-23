"""Data models for the Burgers Zoo integration."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessHours:
    """Opening hours for a single day."""

    is_open: bool
    open_time: str | None
    close_time: str | None
    user_friendly_text: str | None

    @classmethod
    def from_json(cls, data: dict | None) -> "BusinessHours | None":
        if not data:
            return None
        return cls(
            is_open=bool(data.get("isOpen")),  # missing/None isOpen intentionally maps to False
            open_time=data.get("openTime"),
            close_time=data.get("closeTime"),
            user_friendly_text=data.get("userFriendlyText"),
        )


@dataclass(frozen=True)
class Suggestion:
    """Eco-display suggestion for a single day. Raw values, untouched."""

    eco_display: str | None
    title: str | None
    slogan: str | None
    block_title: str | None
    content: str | None
    button_name: str | None
    button_url: str | None
    button_target: str | None
    vimeo_url: str | None
    vimeo_url_mobile: str | None
    primary_header_video: str | None
    primary_header_video_mobile: str | None
    header_video: str | None
    header_video_mobile: str | None
    header_image: str | None
    header_image_mobile: str | None

    @classmethod
    def from_json(cls, data: dict | None) -> "Suggestion | None":
        if not data:
            return None
        button = data.get("button") or {}
        return cls(
            eco_display=data.get("ecoDisplay"),
            title=data.get("ecoDisplayTitle"),
            slogan=data.get("ecoDisplaySlogan"),
            block_title=data.get("ecoDisplayBlockTitle"),
            content=data.get("content"),
            button_name=button.get("name"),
            button_url=button.get("url"),
            button_target=button.get("target"),
            vimeo_url=data.get("vimeoUrl"),
            vimeo_url_mobile=data.get("vimeoUrlMobile"),
            primary_header_video=data.get("primaryHeaderVideo"),
            primary_header_video_mobile=data.get("primaryHeaderVideoMobile"),
            header_video=data.get("headerVideo"),
            header_video_mobile=data.get("headerVideoMobile"),
            header_image=data.get("headerImage"),
            header_image_mobile=data.get("headerImageMobile"),
        )


@dataclass(frozen=True)
class DayData:
    """All data for a single forecast day."""

    temperature: int | None
    chance_of_rain: int | None
    icon_url: str | None
    business_hours: BusinessHours | None
    suggestion: Suggestion | None

    @classmethod
    def from_json(cls, data: dict) -> "DayData":
        return cls(
            temperature=data.get("temperature"),
            chance_of_rain=data.get("chanceOfRain"),
            icon_url=data.get("iconUrl"),
            business_hours=BusinessHours.from_json(data.get("businessHours")),
            suggestion=Suggestion.from_json(data.get("suggestion")),
        )
