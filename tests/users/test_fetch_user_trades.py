"""Tests for :func:`~polymwk.users.trades.fetchUserTrades`."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.users.trades import fetchUserTrades


def test_fetch_user_trades_rejects_empty_user() -> None:
    with pytest.raises(PolymwkError, match="required"):
        fetchUserTrades("", limit=10)


def test_fetch_user_trades_zero_limit_returns_empty() -> None:
    assert fetchUserTrades("0x0000000000000000000000000000000000000001", limit=0) == []


def test_fetch_user_trades_buy_only_conflicts_with_sell_side() -> None:
    with pytest.raises(PolymwkError, match="buy_only"):
        fetchUserTrades("0xabc", buy_only=True, side="SELL")


def test_fetch_user_trades_yes_only_filters() -> None:
    def _row(outcome: str) -> MagicMock:
        r = MagicMock()
        r.proxy_wallet = "0xabc"
        r.side = "BUY"
        r.asset = "t"
        r.condition_id = "0xc"
        r.size = 1.0
        r.price = 0.5
        r.timestamp = datetime(2025, 1, 1, tzinfo=UTC)
        r.title = "T"
        r.slug = "s"
        r.icon = ""
        r.event_slug = "e"
        r.outcome = outcome
        r.outcome_index = 0
        r.name = "n"
        r.pseudonym = "p"
        r.bio = ""
        r.profile_image = ""
        r.profile_image_optimized = ""
        r.transaction_hash = "0xh"
        return r

    with patch("polymwk.users.trades.get_data_client") as mock_get_dc:
        mock_get_dc.return_value.get_trades.return_value = [_row("Yes"), _row("No")]
        out = fetchUserTrades("0xabc", yes_only=True)
    assert len(out) == 1
    assert out[0].outcome == "Yes"


def test_fetch_user_trades_filter_requires_both() -> None:
    with pytest.raises(PolymwkError, match="filter_amount"):
        fetchUserTrades("0xabc", filter_type="CASH")
    with pytest.raises(PolymwkError, match="filter_type"):
        fetchUserTrades("0xabc", filter_amount=1.0)


@patch("polymwk.users.trades.get_data_client")
def test_fetch_user_trades_maps_rows(mock_get_dc) -> None:
    row = MagicMock()
    row.proxy_wallet = "0xabc"
    row.side = "BUY"
    row.asset = "t"
    row.condition_id = "0xc"
    row.size = 100.0
    row.price = 0.5
    row.timestamp = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    row.title = "T?"
    row.slug = "t-q"
    row.icon = ""
    row.event_slug = "e"
    row.outcome = "Yes"
    row.outcome_index = 0
    row.name = "n"
    row.pseudonym = "p"
    row.bio = ""
    row.profile_image = ""
    row.profile_image_optimized = ""
    row.transaction_hash = "0xtx"
    mock_get_dc.return_value.get_trades.return_value = [row]

    out = fetchUserTrades("0xabc", limit=25, offset=3, taker_only=False, side="BUY")

    mock_get_dc.return_value.get_trades.assert_called_once()
    ca = mock_get_dc.return_value.get_trades.call_args
    assert ca[1]["limit"] == 25
    assert ca[1]["offset"] == 3
    assert ca[1]["taker_only"] is False
    assert ca[1]["side"] == "BUY"
    assert len(out) == 1
    assert out[0].wallet == "0xabc"
    assert out[0].market_slug == "t-q"
    assert out[0].value_usd == 50.0


@patch("polymwk.users.trades.get_data_client")
def test_fetch_user_trades_clamps_limit(mock_get_dc) -> None:
    mock_get_dc.return_value.get_trades.return_value = []
    fetchUserTrades("0xabc", limit=9999)
    assert mock_get_dc.return_value.get_trades.call_args[1]["limit"] == 500


@patch("polymwk.users.trades.get_data_client")
def test_fetch_user_trades_http_error(mock_get_dc) -> None:
    import httpx

    mock_get_dc.return_value.get_trades.side_effect = httpx.HTTPError("x")
    with pytest.raises(PolymwkApiError, match="trades"):
        fetchUserTrades("0x0000000000000000000000000000000000000002")
