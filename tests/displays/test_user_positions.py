"""Tests for :mod:`polymwk.displays.users.user_positions`."""

import io
from datetime import UTC, datetime

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.displays.users.user_positions import displayUserPositions
from polymwk.models import Position, UserClosedPosition


def test_display_user_positions_writes_header_and_row() -> None:
    buf = io.StringIO()
    rows = [
        Position(
            wallet="0xabc",
            market_slug="m",
            market_title="Test market title",
            outcome="Yes",
            size=10.0,
            avg_price=0.45,
            current_price=0.55,
            current_value=5.5,
            unrealised_pnl=1.0,
            realised_pnl=0.0,
        )
    ]
    displayUserPositions(rows, stream=buf)
    s = buf.getvalue()
    assert "╔" in s
    assert "User positions" in s
    assert "wallet:" in s
    assert "0xabc" in s
    assert "Test market" in s
    assert "Yes" in s


def test_display_user_positions_empty() -> None:
    buf = io.StringIO()
    displayUserPositions([], stream=buf)
    assert "no positions" in buf.getvalue()


def test_display_user_positions_rejects_wrong_type() -> None:
    with pytest.raises(PolymwkError):
        displayUserPositions("nope", stream=io.StringIO())  # type: ignore[arg-type]


def test_display_user_positions_closed_layout() -> None:
    buf = io.StringIO()
    rows = [
        UserClosedPosition(
            wallet="0xw",
            market_slug="x",
            market_title="Closed market",
            outcome="Yes",
            avg_price=0.5,
            current_price=1.0,
            total_bought=20.0,
            realized_pnl=3.0,
            closed_at=datetime(2025, 1, 2, tzinfo=UTC),
        )
    ]
    displayUserPositions(rows, stream=buf, status="closed")
    s = buf.getvalue()
    assert "bought" in s
    assert "closed" in s
    assert "2025-01-02" in s


def test_display_user_positions_closed_rejects_position_rows() -> None:
    buf = io.StringIO()
    rows = [
        Position(
            wallet="0xw",
            market_slug="x",
            market_title="T",
            outcome="Y",
            size=1.0,
            avg_price=0.5,
            current_price=0.5,
            current_value=1.0,
            unrealised_pnl=0.0,
            realised_pnl=0.0,
        )
    ]
    with pytest.raises(PolymwkError, match="UserClosedPosition"):
        displayUserPositions(rows, stream=buf, status="closed")
