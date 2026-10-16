from collections import Counter
from datetime import date

import pytest

from strava.kudos import (
    count_kudoers,
    kudos_from,
    load_cache,
    months_ago,
    save_cache,
    similar_names,
    sync_kudos,
)


@pytest.mark.parametrize(
    "d, months, want",
    [
        (date(2026, 10, 16), 6, date(2026, 4, 16)),
        (date(2026, 10, 16), 0, date(2026, 10, 16)),
        (date(2026, 3, 15), 6, date(2025, 9, 15)),
        (date(2026, 1, 10), 1, date(2025, 12, 10)),
        (date(2026, 8, 31), 6, date(2026, 2, 28)),
        (date(2028, 8, 31), 6, date(2028, 2, 29)),
        (date(2026, 5, 31), 1, date(2026, 4, 30)),
    ],
)
def test_months_ago(d, months, want):
    assert months_ago(d, months) == want


def test_load_cache_missing_file(tmp_path):
    assert load_cache(tmp_path / "missing.json") == {}


def test_save_and_load_cache(tmp_path):
    path = tmp_path / "nested" / "kudoers.json"
    cache = {"1": {"id": 1, "kudos_count": 2, "kudoers": ["Peter S.", "Ann K."]}}

    save_cache(path, cache)

    assert load_cache(path) == cache


def activity(id: int, kudos_count: int, name: str = "Run") -> dict:
    return {
        "id": id,
        "name": name,
        "start_date": "2026-04-16",
        "sport_type": "Run",
        "kudos_count": kudos_count,
    }


def fetcher(kudoers: dict[int, list[str]], calls: list[int]):
    def fetch(activity_id: int) -> list[str]:
        calls.append(activity_id)
        return kudoers[activity_id]

    return fetch


def test_sync_kudos_fetches_uncached_activities():
    calls, cache = [], {}
    kudoers = {1: ["Peter S.", "Ann K."], 2: ["Peter S."]}

    records = sync_kudos([activity(1, 2), activity(2, 1)], fetcher(kudoers, calls), cache)

    assert records == [
        activity(1, 2) | {"kudoers": ["Peter S.", "Ann K."]},
        activity(2, 1) | {"kudoers": ["Peter S."]},
    ]
    assert calls == [1, 2]
    assert cache == {"1": records[0], "2": records[1]}


def test_sync_kudos_skips_activities_without_kudos():
    calls, cache = [], {}

    records = sync_kudos([activity(3, 0)], fetcher({}, calls), cache)

    assert records == []
    assert calls == []
    assert cache == {}


def test_sync_kudos_uses_cache_when_count_unchanged():
    calls = []
    cache = {"1": {"kudos_count": 2, "kudoers": ["Peter S.", "Ann K."]}}

    records = sync_kudos([activity(1, 2, name="Renamed")], fetcher({}, calls), cache)

    assert calls == []
    assert records == [activity(1, 2, name="Renamed") | {"kudoers": ["Peter S.", "Ann K."]}]
    assert cache["1"]["name"] == "Renamed"


def test_sync_kudos_refetches_when_count_changed():
    calls = []
    cache = {"2": activity(2, 1) | {"kudoers": ["Peter S."]}}

    records = sync_kudos([activity(2, 2)], fetcher({2: ["Peter S.", "Ann K."]}, calls), cache)

    assert calls == [2]
    assert records[0]["kudoers"] == ["Peter S.", "Ann K."]
    assert cache["2"]["kudos_count"] == 2


RECORDS = [
    activity(1, 2) | {"kudoers": ["Peter S.", "Ann K."]},
    activity(2, 1) | {"kudoers": ["Peter S."]},
    activity(3, 1) | {"kudoers": ["Hanna B."]},
]


def test_count_kudoers():
    assert count_kudoers(RECORDS) == Counter({"Peter S.": 2, "Ann K.": 1, "Hanna B.": 1})


@pytest.mark.parametrize(
    "names, want_ids",
    [
        (["Ann K."], [1]),
        (["Peter S."], [1, 2]),
        (["Ann K.", "Hanna B."], [1, 3]),
        (["Nobody X."], []),
    ],
)
def test_kudos_from(names, want_ids):
    assert [r["id"] for r in kudos_from(RECORDS, names)] == want_ids


@pytest.mark.parametrize(
    "name, want",
    [
        ("Hanna S.", ["Hanna B."]),
        ("hanna", ["Hanna B."]),
        ("Peter S", ["Peter S."]),
        ("Peter S.", []),
        ("Nobody", []),
    ],
)
def test_similar_names(name, want):
    assert similar_names(RECORDS, name) == want
