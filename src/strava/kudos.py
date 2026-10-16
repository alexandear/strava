"""Kudos analysis on plain data: activity dicts in, cached activity records out."""

import calendar
import json
from collections import Counter
from collections.abc import Callable, Iterable
from datetime import date
from pathlib import Path


def months_ago(d: date, months: int) -> date:
    year, month = divmod(d.year * 12 + d.month - 1 - months, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def load_cache(path: Path) -> dict:
    """Returns {activity_id: record}; see sync_kudos for the record shape."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache))


def sync_kudos(
    activities: Iterable[dict],
    fetch_kudoers: Callable[[int], list[str]],
    cache: dict,
) -> list[dict]:
    """Returns records for activities with kudos, updating the cache in place.

    Each activity is {"id", "name", "start_date", "sport_type", "kudos_count"}; its record adds
    "kudoers". Kudoers are fetched only when the kudos count differs from the cached one.
    """
    records = []
    for activity in activities:
        if not activity["kudos_count"]:
            continue
        key = str(activity["id"])
        cached = cache.get(key)
        if cached is not None and cached["kudos_count"] == activity["kudos_count"]:
            kudoers = cached["kudoers"]
        else:
            kudoers = fetch_kudoers(activity["id"])
        cache[key] = activity | {"kudoers": kudoers}
        records.append(cache[key])
    return records


def count_kudoers(records: Iterable[dict]) -> Counter:
    return Counter(name for record in records for name in record["kudoers"])


def kudos_from(records: Iterable[dict], names: list[str]) -> list[dict]:
    """Returns records that got kudos from at least one of names."""
    return [r for r in records if any(name in r["kudoers"] for name in names)]


def similar_names(records: Iterable[dict], name: str) -> list[str]:
    """Returns kudoer names sharing the first name, to hint at typos like "Hanna S" vs "Hanna S."."""
    first = name.split()[0].casefold()
    return sorted(
        {n for n in count_kudoers(records) if n.split()[0].casefold() == first and n != name}
    )
