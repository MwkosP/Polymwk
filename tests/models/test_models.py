"""Tests for :mod:`polymwk.models` snapshots and core types."""

from polymwk.models import MarketResolutionSnapshot, MarketRulesSnapshot


def test_market_rules_snapshot_minimal() -> None:
    s = MarketRulesSnapshot(market_slug="x")
    assert s.market_slug == "x"
    assert s.rules_body == ""


def test_market_resolution_snapshot_minimal() -> None:
    s = MarketResolutionSnapshot(market_slug="y")
    assert s.market_slug == "y"
    assert s.condition_id == ""
