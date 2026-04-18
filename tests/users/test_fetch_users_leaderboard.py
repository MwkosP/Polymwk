"""Tests for :func:`~polymwk.users.leaderboard.fetchUsersLeaderboard`."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.users.leaderboard import fetchUsersLeaderboard


def _mock_row(
    rank: int,
    *,
    wallet: str = "0x1111111111111111111111111111111111111111",
    username: str = "trader1",
    pnl: float = 100.0,
    vol: float = 50.0,
) -> MagicMock:
    r = MagicMock()
    r.rank = rank
    r.proxy_wallet = wallet
    r.username = username
    r.x_username = ""
    r.verified_badge = False
    r.pnl = pnl
    r.vol = vol
    r.profile_image = ""
    return r


@patch("polymwk.users.leaderboard.get_data_client")
def test_fetch_users_leaderboard_default_params(mock_get_dc) -> None:
    mock_get_dc.return_value.get_leaderboard_rankings.return_value = [
        _mock_row(1),
    ]

    out = fetchUsersLeaderboard()

    mock_get_dc.return_value.get_leaderboard_rankings.assert_called_once_with(
        category="OVERALL",
        time_period="DAY",
        order_by="PNL",
        limit=25,
        offset=0,
    )
    assert out.timeframe == "today"
    assert out.category == "all"
    assert out.category_label == "All categories"
    assert out.order_by == "pnl"
    assert len(out.entries) == 1
    assert out.entries[0].rank == 1
    assert out.entries[0].username == "trader1"
    assert out.entries[0].pnl == 100.0
    assert out.entries[0].volume_usd == 50.0


@patch("polymwk.users.leaderboard.get_data_client")
def test_fetch_users_leaderboard_maps_timeframe_category_order(mock_get_dc) -> None:
    mock_get_dc.return_value.get_leaderboard_rankings.return_value = []

    fetchUsersLeaderboard(
        timeframe="monthly",
        category="politics",
        order_by="vol",
        limit=50,
        offset=10,
    )

    mock_get_dc.return_value.get_leaderboard_rankings.assert_called_once_with(
        category="POLITICS",
        time_period="MONTH",
        order_by="VOL",
        limit=50,
        offset=10,
    )


@patch("polymwk.users.leaderboard.get_data_client")
def test_fetch_users_leaderboard_accepts_api_category_enum(mock_get_dc) -> None:
    mock_get_dc.return_value.get_leaderboard_rankings.return_value = []

    snap = fetchUsersLeaderboard(category="CRYPTO")

    assert snap.category == "crypto"
    mock_get_dc.return_value.get_leaderboard_rankings.assert_called_once()
    assert (
        mock_get_dc.return_value.get_leaderboard_rankings.call_args[1]["category"]
        == "CRYPTO"
    )


def test_fetch_users_leaderboard_bad_category() -> None:
    with pytest.raises(PolymwkError, match="unknown category"):
        fetchUsersLeaderboard(category="not-a-real-topic")


def test_fetch_users_leaderboard_bad_limit() -> None:
    with pytest.raises(PolymwkError, match="limit"):
        fetchUsersLeaderboard(limit=0)
    with pytest.raises(PolymwkError, match="limit"):
        fetchUsersLeaderboard(limit=51)


@patch("polymwk.users.leaderboard.get_data_client")
def test_fetch_users_leaderboard_http_error(mock_get_dc) -> None:
    mock_get_dc.return_value.get_leaderboard_rankings.side_effect = httpx.HTTPError(
        "x"
    )
    with pytest.raises(PolymwkApiError, match="Leaderboard"):
        fetchUsersLeaderboard()
