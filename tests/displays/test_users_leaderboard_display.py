"""Tests for :func:`~polymwk.displays.users.user_leaderboard.displayUsersLeaderboard`."""

import io

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.displays.users.user_leaderboard import displayUsersLeaderboard
from polymwk.models import LeaderboardEntry, UsersLeaderboardSnapshot


def test_display_users_leaderboard_table() -> None:
    snap = UsersLeaderboardSnapshot(
        timeframe="monthly",
        category="all",
        category_label="All categories",
        order_by="pnl",
        entries=[
            LeaderboardEntry(
                rank=1,
                proxy_wallet="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                username="TopTrader",
                pnl=1_234_567.0,
                volume_usd=9_999.0,
                verified_badge=True,
            ),
            LeaderboardEntry(
                rank=2,
                proxy_wallet="0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                username="",
                pnl=-500.0,
                volume_usd=0.0,
            ),
        ],
    )
    buf = io.StringIO()
    displayUsersLeaderboard(snap, stream=buf)
    text = buf.getvalue()
    assert "Leaderboard" in text
    assert "Monthly" in text
    assert "All categories" in text
    assert "Profit/Loss" in text
    assert "Volume" in text
    assert "TopTrader" in text
    assert "+$1,234,567" in text
    assert "—" in text


def test_display_users_leaderboard_rejects_wrong_type() -> None:
    with pytest.raises(PolymwkError, match="UsersLeaderboardSnapshot"):
        displayUsersLeaderboard("nope", stream=io.StringIO())  # type: ignore[arg-type]
