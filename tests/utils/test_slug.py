"""Tests for :mod:`polymwk.utils.slug`."""

from polymwk.utils.slug import normalize_market_slug


def test_normalize_market_slug_strips() -> None:
    assert normalize_market_slug("  foo-bar  ") == "foo-bar"
