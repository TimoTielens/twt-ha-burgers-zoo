# twt-ha-burgers-zoo

A HACS-installable Home Assistant integration that retrieves data from the
Dutch zoo in Arnhem, Burgers' Zoo — opening hours, expected temperature, and
the daily eco-display suggestion, for today and several days ahead.

## Status

Base / plumbing only. The API client, data coordinator, and config flow are in
place; sensor entities are added in subsequent releases.

## Installation (HACS)

1. Add this repository as a custom repository in HACS (category: Integration).
2. Install "Burgers Zoo".
3. Restart Home Assistant.
4. Add the integration via **Settings → Devices & Services → Add Integration → Burgers Zoo**.

## Configuration

- **Language** — `nl`, `en`, or `de` (default `nl`).
- **Forecast days** — 1–5 (default 3).

Both can be changed later via the integration's options.

## Development

```bash
pip install -r requirements_test.txt
pytest
```
