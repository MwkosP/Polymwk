"""Tests for :mod:`polymwk.utils.event_query`."""

from polymwk.utils.event_query import normalize_event_tag_query


def test_normalize_event_tag_query_dedupes_case_insensitive() -> None:
    assert normalize_event_tag_query(["Bitcoin", "bitcoin", " nvda "]) == [
        "Bitcoin",
        "nvda",
    ]


def test_normalize_event_tag_query_accepts_string() -> None:
    assert normalize_event_tag_query("eth") == ["eth"]
