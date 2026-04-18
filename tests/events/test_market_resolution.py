"""Tests for :mod:`polymwk.events.market_resolution`."""

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.events.market_resolution import fetchMarketResolution


def test_fetch_market_resolution_rejects_empty_slug() -> None:
    with pytest.raises(PolymwkError, match="slug"):
        fetchMarketResolution("")
