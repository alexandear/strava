# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Tooling for working with the owner's personal Strava account (via the Strava API).

Strava's official MCP server (`https://mcp.strava.com/mcp`, OAuth, read-only scopes) is configured in `.mcp.json`; authenticate via `/mcp`.

## Architecture

Python 3.14 project managed by [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`). Strava API access goes through [stravalib](https://github.com/stravalib/stravalib) (pagination, rate limiting, token refresh); output is rendered with [rich](https://github.com/Textualize/rich); `ruff` and `pytest` are dev dependencies.

- `src/strava/api.py` — `client()` returns an authorized `stravalib.Client`: browser OAuth flow on `localhost:8000`, token cached in `~/.config/strava/token.json`.
- `src/strava/kudos.py` — pure logic on primitive data (activity dicts, a fetch function, a cache dict): `sync_kudos` refetches kudoers only when an activity's `kudos_count` changed, plus `count_kudoers`, `kudos_from`, `similar_names`.
- `src/strava/cli.py` — wires stravalib into `kudos.py` and renders rich tables; entry points `top-kudoers` and `kudos-from`. Cache lives in `~/.cache/strava/kudoers.json`. The kudos API returns no athlete ID, so athletes link to Strava search, not profiles.

## Commands

Requires a Strava API app (https://www.strava.com/settings/api) with Authorization Callback Domain `localhost`.

```sh
uv sync                               # create .venv and install
cp .env.example .env                  # then fill in STRAVA_CLIENT_ID / STRAVA_CLIENT_SECRET
uv run --env-file .env top-kudoers --months 6   # athletes who gave kudos, sorted desc
uv run --env-file .env kudos-from "Jane D."     # activities kudoed by given athletes
uv run pytest                         # unit tests (no network, no mocks)
uv run ruff check && uv run ruff format --check
typos                                 # spell check
```
