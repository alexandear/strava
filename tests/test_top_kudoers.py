from collections import Counter
from datetime import date

import pytest
from rich.console import Console

from strava.top_kudoers import (
    count_kudoers,
    kudos_table,
    load_cache,
    months_ago,
    save_cache,
    search_url,
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


def test_search_url():
    assert search_url("Peter S.") == "https://www.strava.com/athletes/search?text=Peter+S."
    assert search_url("Олег К.") == (
        "https://www.strava.com/athletes/search?text=%D0%9E%D0%BB%D0%B5%D0%B3+%D0%9A."
    )


def test_load_cache_missing_file(tmp_path):
    assert load_cache(tmp_path / "missing.json") == {}


def test_save_and_load_cache(tmp_path):
    path = tmp_path / "nested" / "kudoers.json"
    cache = {"1": {"kudos_count": 2, "kudoers": ["Peter S.", "Ann K."]}}

    save_cache(path, cache)

    assert load_cache(path) == cache


KUDOERS = {
    1: ["Peter S.", "Ann K."],
    2: ["Peter S."],
}


def fetcher(kudoers: dict[int, list[str]], calls: list[int]):
    def fetch(activity_id: int) -> list[str]:
        calls.append(activity_id)
        return kudoers[activity_id]

    return fetch


def test_count_kudoers_fetches_uncached_activities():
    calls, cache = [], {}

    counts = count_kudoers([(1, 2), (2, 1)], fetcher(KUDOERS, calls), cache)

    assert counts == Counter({"Peter S.": 2, "Ann K.": 1})
    assert calls == [1, 2]
    assert cache == {
        "1": {"kudos_count": 2, "kudoers": ["Peter S.", "Ann K."]},
        "2": {"kudos_count": 1, "kudoers": ["Peter S."]},
    }


def test_count_kudoers_skips_activities_without_kudos():
    calls, cache = [], {}

    counts = count_kudoers([(3, 0)], fetcher({}, calls), cache)

    assert counts == Counter()
    assert calls == []
    assert cache == {}


def test_count_kudoers_uses_cache_when_count_unchanged():
    calls = []
    cache = {"1": {"kudos_count": 2, "kudoers": ["Peter S.", "Ann K."]}}

    counts = count_kudoers([(1, 2)], fetcher({}, calls), cache)

    assert counts == Counter({"Peter S.": 1, "Ann K.": 1})
    assert calls == []


def test_count_kudoers_refetches_when_count_changed():
    calls = []
    cache = {"2": {"kudos_count": 1, "kudoers": ["Peter S."]}}
    kudoers = {2: ["Peter S.", "Ann K."]}

    counts = count_kudoers([(2, 2)], fetcher(kudoers, calls), cache)

    assert counts == Counter({"Peter S.": 1, "Ann K.": 1})
    assert calls == [2]
    assert cache["2"] == {"kudos_count": 2, "kudoers": ["Peter S.", "Ann K."]}


def test_kudos_table_sorted_desc():
    console = Console(width=120, record=True)

    console.print(kudos_table(Counter({"Ann K.": 1, "Peter S.": 5, "Jane D.": 3}), 6))

    lines = console.export_text().splitlines()
    assert "Kudos in the last 6 months" in lines[0]
    rows = [line for line in lines if "athletes/search" in line]
    assert [row.split("│")[1:4] for row in rows] == [
        [" 1 ", " Peter S. ", "     5 "],
        [" 2 ", " Jane D.  ", "     3 "],
        [" 3 ", " Ann K.   ", "     1 "],
    ]
