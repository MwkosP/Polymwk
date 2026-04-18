"""Tests for :mod:`polymwk.events.market_rules`."""

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.events.market_rules import fetchMarketRules


def test_fetch_market_rules_rejects_empty_slug() -> None:
    with pytest.raises(PolymwkError, match="slug"):
        fetchMarketRules("")
