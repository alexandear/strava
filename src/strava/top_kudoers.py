"""Prints athletes who gave kudos to your activities, sorted by kudos count."""

import argparse
import calendar
import json
import urllib.parse
from collections import Counter
from collections.abc import Callable, Iterable
from datetime import date, datetime, time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from strava import api

CACHE_FILE = Path.home() / ".cache" / "strava" / "kudoers.json"


def months_ago(d: date, months: int) -> date:
    year, month = divmod(d.year * 12 + d.month - 1 - months, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def load_cache(path: Path) -> dict:
    """Returns {activity_id: {"kudos_count": int, "kudoers": [name, ...]}}."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache))


def count_kudoers(
    activities: Iterable[tuple[int, int]],
    fetch_kudoers: Callable[[int], list[str]],
    cache: dict,
) -> Counter:
    """Counts kudos per athlete name from (activity_id, kudos_count) pairs.

    Kudoers are fetched only for activities whose kudos count differs from the cache.
    """
    counts = Counter()
    for activity_id, kudos_count in activities:
        if not kudos_count:
            continue
        key = str(activity_id)
        cached = cache.get(key)
        if cached is None or cached["kudos_count"] != kudos_count:
            kudoers = fetch_kudoers(activity_id)
            cached = cache[key] = {"kudos_count": kudos_count, "kudoers": kudoers}
        counts.update(cached["kudoers"])
    return counts


def search_url(name: str) -> str:
    """The kudos API returns no athlete ID, so link to Strava athlete search instead of a profile."""
    return f"https://www.strava.com/athletes/search?{urllib.parse.urlencode({'text': name})}"


def kudos_table(counts: Counter, months: int) -> Table:
    table = Table(title=f"Kudos in the last {months} months")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Athlete", style="bold")
    table.add_column("Kudos", justify="right", style="orange1")
    table.add_column("Search link", overflow="fold")
    for rank, (name, n) in enumerate(counts.most_common(), 1):
        url = search_url(name)
        table.add_row(str(rank), name, str(n), f"[link={url}]{url}[/link]")
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--months", type=int, default=6, help="look back this many months (default: 6)"
    )
    args = parser.parse_args()

    client = api.client()
    after = datetime.combine(months_ago(date.today(), args.months), time()).astimezone()
    activities = ((a.id, a.kudos_count) for a in client.get_activities(after=after))

    def fetch_kudoers(activity_id: int) -> list[str]:
        return [f"{a.firstname} {a.lastname}" for a in client.get_activity_kudos(activity_id)]

    cache = load_cache(CACHE_FILE)
    try:
        counts = count_kudoers(activities, fetch_kudoers, cache)
    finally:
        save_cache(CACHE_FILE, cache)
    Console().print(kudos_table(counts, args.months))
