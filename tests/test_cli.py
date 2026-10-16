from collections import Counter

from rich.console import Console

from strava.cli import activity_url, kudos_from_table, search_url, top_kudoers_table


def render(table) -> list[str]:
    console = Console(width=140, record=True)
    console.print(table)
    return console.export_text().splitlines()


def test_search_url():
    assert search_url("Peter S.") == "https://www.strava.com/athletes/search?text=Peter+S."
    assert search_url("Олег К.") == (
        "https://www.strava.com/athletes/search?text=%D0%9E%D0%BB%D0%B5%D0%B3+%D0%9A."
    )


def test_activity_url():
    assert activity_url(18128641071) == "https://www.strava.com/activities/18128641071"


def test_top_kudoers_table_sorted_desc():
    lines = render(top_kudoers_table(Counter({"Ann K.": 1, "Peter S.": 5, "Jane D.": 3}), 6))

    assert "Kudos in the last 6 months" in lines[0]
    rows = [line for line in lines if "athletes/search" in line]
    assert [row.split("│")[1:4] for row in rows] == [
        [" 1 ", " Peter S. ", "     5 "],
        [" 2 ", " Jane D.  ", "     3 "],
        [" 3 ", " Ann K.   ", "     1 "],
    ]


def test_kudos_from_table_marks_each_athlete():
    records = [
        {
            "id": 1,
            "name": "Long Ride",
            "start_date": "2026-05-06",
            "sport_type": "Ride",
            "kudos_count": 35,
            "kudoers": ["Hanna S.", "Ann K."],
        },
        {
            "id": 2,
            "name": "Cross",
            "start_date": "2026-05-05",
            "sport_type": "Run",
            "kudos_count": 33,
            "kudoers": ["Hanna S."],
        },
    ]

    lines = render(kudos_from_table(records, ["Hanna S.", "Ann K."], 6))

    assert "Kudos from Hanna S., Ann K. in the last 6 months" in lines[0]
    rows = [[cell.strip() for cell in line.split("│")[1:-1]] for line in lines if "2026-" in line]
    assert rows == [
        ["2026-05-06", "Ride", "Long Ride", "35", "✓", "✓"],
        ["2026-05-05", "Run", "Cross", "33", "✓", ""],
    ]
    assert "Hanna S.: 2 · Ann K.: 1" in lines[-1]
