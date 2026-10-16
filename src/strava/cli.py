"""Command-line entry points: top-kudoers and kudos-from."""

import argparse
import urllib.parse
from collections import Counter
from datetime import date, datetime, time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from strava import api, kudos

CACHE_FILE = Path.home() / ".cache" / "strava" / "kudoers.json"


def search_url(name: str) -> str:
    """The kudos API returns no athlete ID, so link to Strava athlete search instead of a profile."""
    return f"https://www.strava.com/athletes/search?{urllib.parse.urlencode({'text': name})}"


def activity_url(activity_id: int) -> str:
    return f"https://www.strava.com/activities/{activity_id}"


def top_kudoers_table(counts: Counter, months: int) -> Table:
    table = Table(title=f"Kudos in the last {months} months")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Athlete", style="bold")
    table.add_column("Kudos", justify="right", style="orange1")
    table.add_column("Search link", overflow="fold")
    for rank, (name, n) in enumerate(counts.most_common(), 1):
        url = search_url(name)
        table.add_row(str(rank), name, str(n), f"[link={url}]{url}[/link]")
    return table


def kudos_from_table(records: list[dict], names: list[str], months: int) -> Table:
    table = Table(
        title=f"Kudos from {', '.join(names)} in the last {months} months",
        caption=" · ".join(
            f"{name}: {sum(name in r['kudoers'] for r in records)}" for name in names
        ),
    )
    table.add_column("Date", style="dim")
    table.add_column("Type")
    table.add_column("Activity", style="bold")
    table.add_column("Kudos", justify="right", style="orange1")
    for name in names:
        table.add_column(name, justify="center", style="green")
    for r in records:
        checks = ["✓" if name in r["kudoers"] else "" for name in names]
        activity = f"[link={activity_url(r['id'])}]{r['name']}[/link]"
        table.add_row(r["start_date"], r["sport_type"], activity, str(r["kudos_count"]), *checks)
    return table


def _parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--months", type=int, default=6, help="look back this many months (default: 6)"
    )
    return parser


def _sync(months: int) -> list[dict]:
    """Fetches activities in the window and returns their kudos records, using the cache."""
    client = api.client()
    after = datetime.combine(kudos.months_ago(date.today(), months), time()).astimezone()
    activities = (
        {
            "id": a.id,
            "name": a.name,
            "start_date": a.start_date_local.date().isoformat(),
            "sport_type": a.sport_type.root if a.sport_type else "",
            "kudos_count": a.kudos_count,
        }
        for a in client.get_activities(after=after)
    )

    def fetch_kudoers(activity_id: int) -> list[str]:
        return [f"{a.firstname} {a.lastname}" for a in client.get_activity_kudos(activity_id)]

    cache = kudos.load_cache(CACHE_FILE)
    try:
        return kudos.sync_kudos(activities, fetch_kudoers, cache)
    finally:
        kudos.save_cache(CACHE_FILE, cache)


def top_kudoers():
    """Prints athletes who gave kudos to your activities, sorted by kudos count."""
    args = _parser(top_kudoers.__doc__).parse_args()
    records = _sync(args.months)
    Console().print(top_kudoers_table(kudos.count_kudoers(records), args.months))


def kudos_from():
    """Prints your activities that got kudos from the given athletes."""
    parser = _parser(kudos_from.__doc__)
    parser.add_argument(
        "names", nargs="+", help='athlete names as shown by top-kudoers, e.g. "Hanna S."'
    )
    args = parser.parse_args()
    records = _sync(args.months)

    console = Console()
    for name in args.names:
        if any(name in r["kudoers"] for r in records):
            continue
        hint = ", ".join(kudos.similar_names(records, name))
        console.print(
            f"[yellow]No kudos from {name!r}.[/yellow]" + (f" Similar: {hint}" if hint else "")
        )
    console.print(kudos_from_table(kudos.kudos_from(records, args.names), args.names, args.months))
