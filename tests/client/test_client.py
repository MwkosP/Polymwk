"""Tests for :mod:`polymwk.client`."""

from polymwk.client import Polymarket


def test_polymarket_exposes_resolver() -> None:
    p = Polymarket()
    assert p.resolver is not None
