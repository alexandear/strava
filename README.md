# strava

Tooling for working with a personal Strava account via the [Strava API](https://developers.strava.com/docs/reference/), built on [stravalib](https://github.com/stravalib/stravalib).

## Tools

- `top-kudoers` — lists athletes who gave kudos to your activities over the last N months, sorted by kudos count (descending).

## Setup

Requires [uv](https://docs.astral.sh/uv/).

1. Create a Strava API app at <https://www.strava.com/settings/api> with **Authorization Callback Domain** set to `localhost`.
2. Install dependencies and configure credentials:

   ```sh
   uv sync
   cp .env.example .env   # fill in STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET
   ```

## Usage

```sh
uv run --env-file .env top-kudoers             # last 6 months
uv run --env-file .env top-kudoers --months 12
```

Example output:

```text
                         Kudos in the last 6 months
┏━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Athlete ┃ Kudos ┃ Search link                                         ┃
┡━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ Jane D. │    42 │ https://www.strava.com/athletes/search?text=Jane+D. │
│ 2 │ John S. │    37 │ https://www.strava.com/athletes/search?text=John+S. │
└───┴─────────┴───────┴─────────────────────────────────────────────────────┘
```

On the first run a browser tab opens to authorize the app (scope `activity:read_all`). The token is cached in `~/.config/strava/token.json` and refreshed automatically.

Notes:

- Strava only exposes the kudoer's first name and last initial (no athlete ID), so different athletes with the same short name are counted together, and links point to Strava athlete search rather than a profile.
- Kudoers are cached per activity in `~/.cache/strava/kudoers.json` and refetched only when the activity's kudos count changes. Delete the file to start fresh.
- Each uncached activity with kudos costs one API request. The default rate limit is 100 requests per 15 minutes, so long periods take a while; the client waits out the limit automatically.

## Development

```sh
uv run pytest
uv run ruff check
uv run ruff format
typos
```
