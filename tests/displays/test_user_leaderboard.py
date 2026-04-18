"""Tests for :mod:`polymwk.displays.users.user_leaderboard`."""

import io

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.displays.users.user_leaderboard import displayUserLeaderboardRank
from polymwk.models import UserLeaderboardRank


def test_display_user_leaderboard_writes_rank_and_stats() -> None:
    buf = io.StringIO()
    snap = UserLeaderboardRank(
        proxy_wallet="0xw",
        rank=100,
        metric="profit",
        window="30d",
        ranked_amount=-50.0,
        other_metric_amount=1_234.56,
        name="N",
        pseudonym="",
    )
    displayUserLeaderboardRank(snap, stream=buf)
    s = buf.getvalue()
    assert "Leaderboard" in s
    assert "0xw" in s
    assert "#100" in s
    assert "Profit" in s or "PnL" in s
    assert "Volume" in s


def test_display_user_leaderboard_rejects_wrong_type() -> None:
    with pytest.raises(PolymwkError):
        displayUserLeaderboardRank("nope", stream=io.StringIO())  # type: ignore[arg-type]
