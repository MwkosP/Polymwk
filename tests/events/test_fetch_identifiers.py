"""Single-entity fetches: slug vs id / market identifier exclusivity."""

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.events.fetch import fetchEvent
from polymwk.events.markets import fetchMarket
from polymwk.events.series import fetchSerie


def test_fetch_event_rejects_both_slug_and_id() -> None:
    with pytest.raises(PolymwkError, match="not both"):
        fetchEvent("a", id="1")


def test_fetch_event_requires_identifier() -> None:
    with pytest.raises(PolymwkError, match="slug"):
        fetchEvent()


def test_fetch_market_rejects_multiple_ids() -> None:
    with pytest.raises(PolymwkError, match="exactly one"):
        fetchMarket("a", id="1")


def test_fetch_market_requires_identifier() -> None:
    with pytest.raises(PolymwkError, match="market slug"):
        fetchMarket()


def test_fetch_serie_rejects_both() -> None:
    with pytest.raises(PolymwkError, match="not both"):
        fetchSerie("a", id="1")
