"""Tests for :mod:`polymwk.displays.users.user_trades`."""

import io
from datetime import UTC, datetime

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.displays.users.user_trades import displayUserTrades
from polymwk.models import Trade


def test_display_user_trades_header_and_row() -> None:
    buf = io.StringIO()
    rows = [
        Trade(
            wallet="0xw",
            market_slug="m",
            market_title="Some market",
            side="BUY",
            outcome="Yes",
            price=0.5,
            size=10.0,
            value_usd=5.0,
            timestamp=datetime.now(UTC),
            tx_hash="0xabc123",
        )
    ]
    displayUserTrades(rows, stream=buf)
    s = buf.getvalue()
    assert "╔" in s
    assert "User trades" in s
    assert "0xw" in s
    assert "BUY" in s


def test_display_user_trades_empty() -> None:
    buf = io.StringIO()
    displayUserTrades([], stream=buf)
    assert "no trades" in buf.getvalue()


def test_display_user_trades_rejects_bad_sequence() -> None:
    with pytest.raises(PolymwkError):
        displayUserTrades("x", stream=io.StringIO())  # type: ignore[arg-type]
