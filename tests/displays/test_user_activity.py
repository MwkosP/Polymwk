"""Tests for :mod:`polymwk.displays.users.user_activity`."""

import io
from datetime import UTC, datetime

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.displays.users.user_activity import displayUserActivity
from polymwk.models import Activity


def test_display_user_activity_header_and_row() -> None:
    buf = io.StringIO()
    rows = [
        Activity(
            wallet="0xw",
            type="TRADE",
            timestamp=datetime.now(UTC),
            market_slug="m",
            market_title="Some market",
            outcome="Yes",
            side="BUY",
            size=1.0,
            usdc_size=10.0,
            price=0.5,
        )
    ]
    displayUserActivity(rows, stream=buf)
    s = buf.getvalue()
    assert "╔" in s
    assert "User activity" in s
    assert "0xw" in s
    assert "TRADE" in s


def test_display_user_activity_empty() -> None:
    buf = io.StringIO()
    displayUserActivity([], stream=buf)
    assert "no activity" in buf.getvalue()


def test_display_user_activity_rejects_bad_sequence() -> None:
    with pytest.raises(PolymwkError):
        displayUserActivity("x", stream=io.StringIO())  # type: ignore[arg-type]
