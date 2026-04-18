"""Tests for :mod:`polymwk.constants`."""

from polymwk.constants import DEFAULT_EVENT_LIMIT, DEFAULT_SEARCH_LIMIT


def test_default_limits_positive() -> None:
    assert DEFAULT_EVENT_LIMIT >= 1
    assert DEFAULT_SEARCH_LIMIT >= 1
