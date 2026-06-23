# Burgers Zoo Home Assistant Integration — Base Design

**Date:** 2026-06-23
**Status:** Approved (design)
**Scope:** Solid base / plumbing only. No entities yet — sensors are added later, feature by feature.

## Goal

A HACS-installable Home Assistant custom integration that retrieves data from
Burgers' Zoo (Arnhem, NL) via its public weather API. This document covers only
the **base**: API client, data coordinator, config flow, models, and the full
test/CI harness. It deliberately creates **no entities** — those follow as
separate features.

## Background

A prior attempt (`origin/init` branch) used a YAML-based setup
(`config_flow: false`) that wrote states directly via `hass.states.async_set`
on HA startup plus a daily 01:00 refresh. Problems we are correcting:

- Fake states instead of real entities (no proper entity registry, no device).
- No `DataUpdateCoordinator` — no shared polling, no unified error handling.
- No config flow (no UI setup, no reconfiguration).
- No tests, no CI.
- `system_health.py` referenced a wrong entity id and was never registered.
- `iot_class` was `local_polling` (wrong — it polls an external cloud API).

We start fresh on a new branch using modern HA patterns.

## API Reference

Endpoint (no authentication, no secrets):

```
https://www.burgerszoo.nl/api/weather/{day}?culture={culture}
```

- `{day}`: integer day offset. **Valid range 0–4** (0 = today). Days 5+ return
  HTTP 200 but an all-`null` payload, so they carry no usable data and must not
  be requested.
- `{culture}`: `nl-NL`, `en-US`, or `de-DE`.

Example payload (`/api/weather/0?culture=nl-NL`):

```json
{
  "temperature": 30,
  "iconUrl": "FullSun",
  "suggestion": {
    "ecoDisplayTitle": "Ontdek de Oost-Afrikaanse savanne!",
    "ecoDisplaySlogan": "In één dag op wereldreis!",
    "ecoDisplayBlockTitle": "Tip! Ga op safari op onze savannevlakte",
    "content": "<p>{{dayText}} wordt het {{temperatureText}} graden: ideaal weer om de giraffen...</p>",
    "button": { "name": "Bezoek de savannevlakte", "target": null, "url": "https://www.burgerszoo.nl/reserveren" },
    "ecoDisplay": "safari",
    "vimeoUrl": "", "vimeoUrlMobile": "",
    "primaryHeaderVideo": "", "primaryHeaderVideoMobile": "",
    "headerVideo": "/media/jcadvkml/safari-1-2-small.mp4",
    "headerVideoMobile": "/media/mjojmyus/safari-1-2-small.mp4",
    "headerImage": "/media/djnj14z5/safari-still.jpg?width=1920&v=1db7d6a4c2e4df0",
    "headerImageMobile": null
  },
  "businessHours": {
    "isOpen": true,
    "openTime": "09:00:00",
    "closeTime": "18:00:00",
    "userFriendlyText": "09:00 tot 18:00"
  },
  "chanceOfRain": 10
}
```

Notes:
- `content` contains HTML and `{{dayText}}` / `{{temperatureText}}` placeholders.
  The base preserves it **raw** — substitution and HTML stripping are later
  sensor concerns.
- Media/video fields may be empty strings or `null`.

## Architecture

### Approach

Single `DataUpdateCoordinator` that fetches all configured days in one refresh
cycle (`asyncio.gather` over indices `0..N-1`) and stores `{day_index: DayData}`.
Rejected alternatives: one coordinator per day (needless complexity for a
once-daily feed) and entity-level polling (the prior branch's approach — not
real entities, no shared session/error handling).

### Component structure

```
custom_components/twt_ha_burgers_zoo/
├── __init__.py          # async_setup_entry / async_unload_entry / async_reload_entry
├── api.py               # BurgersZooApiClient over HA's shared aiohttp session
├── coordinator.py       # BurgersZooDataUpdateCoordinator
├── config_flow.py       # config flow + options flow (language, forecast days)
├── const.py             # DOMAIN, defaults, culture map, conf keys
├── models.py            # dataclasses: DayData, BusinessHours, Suggestion
├── manifest.json
├── strings.json
└── translations/
    ├── en.json
    └── nl.json
```

No `sensor.py` yet — the platforms list starts empty; the first sensor feature
adds `Platform.SENSOR`.

### Manifest

```json
{
  "domain": "twt_ha_burgers_zoo",
  "name": "Burgers Zoo",
  "version": "0.1.0",
  "codeowners": ["@TimoTielens"],
  "documentation": "https://github.com/TimoTielens/twt-ha-burgers-zoo",
  "issue_tracker": "https://github.com/TimoTielens/twt-ha-burgers-zoo/issues",
  "integration_type": "service",
  "iot_class": "cloud_polling",
  "config_flow": true,
  "requirements": []
}
```

- `requirements: []` — uses HA's bundled aiohttp via the shared client session.
- Single config entry only: `async_set_unique_id("burgers_zoo")` + abort if
  already configured.

## Components

### `models.py`

Frozen dataclasses mirroring the API, raw values preserved. Parsing is
defensive: every field via `.get()`, missing nested objects → `None`, never
raises on a partial/all-null payload.

```python
@dataclass(frozen=True)
class BusinessHours:
    is_open: bool
    open_time: str | None        # "09:00:00"
    close_time: str | None
    user_friendly_text: str | None

@dataclass(frozen=True)
class Suggestion:
    eco_display: str | None              # "safari"
    title: str | None
    slogan: str | None
    block_title: str | None
    content: str | None                  # raw HTML w/ placeholders, untouched
    button_name: str | None
    button_url: str | None
    button_target: str | None
    vimeo_url: str | None
    vimeo_url_mobile: str | None
    primary_header_video: str | None
    primary_header_video_mobile: str | None
    header_video: str | None             # "/media/.../safari-1-2-small.mp4"
    header_video_mobile: str | None
    header_image: str | None
    header_image_mobile: str | None

@dataclass(frozen=True)
class DayData:
    temperature: int | None
    chance_of_rain: int | None
    icon_url: str | None                 # "FullSun"
    business_hours: BusinessHours | None
    suggestion: Suggestion | None
```

Media paths are stored raw (relative, as returned). Absolute-URL construction
is a later attribute concern.

### `api.py`

`BurgersZooApiClient` takes an injected `aiohttp.ClientSession` (HA's shared
session via `async_get_clientsession`).

- `async def async_get_day(day: int) -> DayData`
- `async def async_get_days(count: int) -> dict[int, DayData]` — `asyncio.gather`
  over `0..count-1`.
- Culture resolved from configured language: `nl→nl-NL`, `en→en-US`, `de→de-DE`.
- Requests wrapped in a timeout (`async_timeout`).
- Error normalization into two custom exceptions:
  - `BurgersZooConnectionError` — network error / timeout (`aiohttp.ClientError`,
    `asyncio.TimeoutError`).
  - `BurgersZooApiError` — non-200 status or unparseable payload.

The client parses but does not interpret (no placeholder substitution, no
open/closed logic, no HTML stripping).

### `coordinator.py`

`BurgersZooDataUpdateCoordinator(DataUpdateCoordinator[dict[int, DayData]])`:

- `_async_update_data()` calls `client.async_get_days(forecast_days)`, catching
  `BurgersZooConnectionError` / `BurgersZooApiError` and re-raising as
  `UpdateFailed`.
- `update_interval`: **fixed at 1 hour** (not user-configurable). The feed
  changes daily, but `isOpen` flips at open/close times, so hourly keeps that
  fresh without hammering the API.

### `__init__.py`

- `async_setup_entry`: build client (shared session) + coordinator,
  `await coordinator.async_config_entry_first_refresh()`, store on
  `entry.runtime_data`, forward to platforms (initially empty list).
- `async_unload_entry`: unload platforms cleanly.
- `async_reload_entry`: options-update listener so changing language /
  forecast days reloads the entry.

### `config_flow.py`

- **Config flow** (`user` step): form with
  - `language`: select nl / en / de, default `nl`.
  - `forecast_days`: int **1–5**, default 3.
  Validates by performing a single live `async_get_day(0)` test call; abort with
  `cannot_connect` on failure. Single instance enforced via unique id.
- **Options flow**: same two fields, editable after setup; saving triggers
  reload via the options-update listener.
- `strings.json` + `translations/{en,nl}.json` for labels and error messages.

## Configuration

| Option          | Where                 | Values            | Default |
|-----------------|-----------------------|-------------------|---------|
| `language`      | config + options flow | `nl` / `en` / `de`| `nl`    |
| `forecast_days` | config + options flow | `1`–`5`           | `3`     |
| update interval | fixed (code)          | 1 hour            | —       |

## Error Handling

- API layer raises `BurgersZooConnectionError` / `BurgersZooApiError`.
- Coordinator converts both to `UpdateFailed`; HA then marks entities
  unavailable and retries on the next interval.
- Config flow surfaces failures as a `cannot_connect` form error.
- Partial / all-null payloads never raise — parsed into dataclasses with `None`
  fields.

## Testing

`pytest` + `pytest-homeassistant-custom-component`; HTTP mocked with
`aioresponses`.

- `conftest.py`: `enable_custom_integrations` fixture, sample API JSON payloads
  (full, partial, all-null), mock aiohttp responder.
- `test_api.py`: parsing (full payload, partial/missing fields, media fields,
  all-null day), culture→URL mapping, connection vs API error mapping.
- `test_coordinator.py`: multi-day gather → `dict[int, DayData]`; failure →
  `UpdateFailed`.
- `test_config_flow.py`: happy path, `cannot_connect`, single-instance abort,
  options flow updates + reload.
- `test_init.py`: setup + unload entry lifecycle.

## CI / Packaging

- `hacs.json` at repo root → HACS-installable.
- `.github/workflows/validate.yml`: Hassfest + HACS Action.
- `.github/workflows/test.yml`: pytest on the supported Python version.

## Out of Scope (future features)

- Any entities (`sensor.py` and beyond) — added one feature at a time.
- Placeholder substitution (`{{dayText}}`, `{{temperatureText}}`).
- HTML stripping of `content`.
- Open/closed state logic and friendly attributes.
- Absolute-URL construction for media paths.
- `system_health` registration.
```
