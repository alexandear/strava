# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Tooling for working with the owner's personal Strava account (via the Strava API).

Strava's official MCP server (`https://mcp.strava.com/mcp`, OAuth, read-only scopes) is configured in `.mcp.json`; authenticate via `/mcp`.

## Architecture

Python 3.14 project managed by [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`). Strava API access goes through [stravalib](https://github.com/stravalib/stravalib) (pagination, rate limiting, token refresh); output is rendered with [rich](https://github.com/Textualize/rich); `ruff` and `pytest` are dev dependencies. Core logic in `top_kudoers.py` takes primitive data (`(activity_id, kudos_count)` pairs, a fetch function); stravalib is wired only in `main()`.

- `src/strava/api.py` — `client()` returns an authorized `stravalib.Client`: browser OAuth flow on `localhost:8000`, token cached in `~/.config/strava/token.json`.
- `src/strava/top_kudoers.py` — CLI built on `api.py`, exposed as the `top-kudoers` script. Caches kudoers per activity in `~/.cache/strava/kudoers.json`, invalidated when the activity's `kudos_count` changes. The kudos API returns no athlete ID, so output links to athlete search, not profiles.

## Commands

Requires a Strava API app (https://www.strava.com/settings/api) with Authorization Callback Domain `localhost`.

```sh
uv sync                               # create .venv and install
cp .env.example .env                  # then fill in STRAVA_CLIENT_ID / STRAVA_CLIENT_SECRET
uv run --env-file .env top-kudoers --months 6   # athletes who gave kudos, sorted desc
uv run pytest                         # unit tests (no network, no mocks)
uv run ruff check && uv run ruff format --check
typos                                 # spell check
```
