"""Tests for :func:`~polymwk.users.leaderboard.fetchUserLeaderboardRank`."""

from unittest.mock import MagicMock, patch

import pytest

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.users.leaderboard import fetchUserLeaderboardRank


def test_fetch_user_leaderboard_rejects_empty_user() -> None:
    with pytest.raises(PolymwkError, match="required"):
        fetchUserLeaderboardRank("")


@patch("polymwk.users.leaderboard.get_data_client")
def test_fetch_user_leaderboard_rank_and_cross_metric(mock_get_dc) -> None:
    rank = MagicMock()
    rank.proxy_wallet = "0xabc"
    rank.rank = 42
    rank.amount = 1000.0
    rank.name = "Trader"
    rank.pseudonym = ""
    rank.bio = ""
    rank.profile_image = ""

    other = MagicMock()
    other.amount = 500_000.0

    mock_get_dc.return_value.get_leaderboard_user_rank.return_value = rank
    mock_get_dc.return_value.get_user_metric.return_value = other

    out = fetchUserLeaderboardRank("0xabc", metric="profit", window="all")

    mock_get_dc.return_value.get_leaderboard_user_rank.assert_called_once()
    mock_get_dc.return_value.get_user_metric.assert_called_once()
    mm = mock_get_dc.return_value.get_user_metric.call_args
    assert mm[1]["metric"] == "volume"

    assert out.proxy_wallet == "0xabc"
    assert out.rank == 42
    assert out.metric == "profit"
    assert out.ranked_amount == 1000.0
    assert out.other_metric_amount == 500_000.0


@patch("polymwk.users.leaderboard.get_data_client")
def test_fetch_user_leaderboard_skips_cross_when_disabled(mock_get_dc) -> None:
    rank = MagicMock()
    rank.proxy_wallet = "0xabc"
    rank.rank = 1
    rank.amount = 1.0
    rank.name = ""
    rank.pseudonym = "x"
    rank.bio = ""
    rank.profile_image = ""
    mock_get_dc.return_value.get_leaderboard_user_rank.return_value = rank

    out = fetchUserLeaderboardRank("0xabc", include_cross_metric=False)

    mock_get_dc.return_value.get_user_metric.assert_not_called()
    assert out.other_metric_amount is None


@patch("polymwk.users.leaderboard.get_data_client")
def test_fetch_user_leaderboard_rank_http_error(mock_get_dc) -> None:
    import httpx

    mock_get_dc.return_value.get_leaderboard_user_rank.side_effect = httpx.HTTPError("x")
    with pytest.raises(PolymwkApiError, match="Leaderboard"):
        fetchUserLeaderboardRank("0x0000000000000000000000000000000000000001")
