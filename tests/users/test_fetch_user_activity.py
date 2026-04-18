"""Tests for :func:`~polymwk.users.activity.fetchUserActivity`."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.users.activity import fetchUserActivity


def test_fetch_user_activity_buy_sell_mutually_exclusive() -> None:
    with pytest.raises(PolymwkError, match="buy_only"):
        fetchUserActivity("0xabc", buy_only=True, sell_only=True)


def test_fetch_user_activity_rejects_empty_user() -> None:
    with pytest.raises(PolymwkError, match="required"):
        fetchUserActivity("", limit=10)


def test_fetch_user_activity_zero_limit_returns_empty() -> None:
    out = fetchUserActivity("0x0000000000000000000000000000000000000001", limit=0)
    assert out == []


@patch("polymwk.users.activity.get_data_client")
def test_fetch_user_activity_buy_only_sets_side(mock_get_dc) -> None:
    mock_get_dc.return_value.get_activity.return_value = []
    fetchUserActivity("0xabc", buy_only=True)
    assert mock_get_dc.return_value.get_activity.call_args[1]["side"] == "BUY"


@patch("polymwk.users.activity.get_data_client")
def test_fetch_user_activity_yes_only_filters_client_side(mock_get_dc) -> None:
    def _row(outcome: str) -> MagicMock:
        r = MagicMock()
        r.proxy_wallet = "0xabc"
        r.type = "TRADE"
        r.timestamp = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
        r.condition_id = "0xc"
        r.size = 1.0
        r.usdc_size = 1.0
        r.price = 0.5
        r.asset = "t"
        r.side = "BUY"
        r.outcome_index = 0
        r.title = "T"
        r.slug = "s"
        r.icon = ""
        r.event_slug = "e"
        r.outcome = outcome
        r.name = "n"
        r.pseudonym = "p"
        r.bio = ""
        r.profile_image = ""
        r.profile_image_optimized = ""
        r.transaction_hash = "0xh"
        return r

    mock_get_dc.return_value.get_activity.return_value = [
        _row("Yes"),
        _row("No"),
    ]
    out = fetchUserActivity("0xabc", yes_only=True, limit=50)
    assert len(out) == 1
    assert out[0].outcome == "Yes"


@patch("polymwk.users.activity.get_data_client")
def test_fetch_user_activity_maps_rows(mock_get_dc) -> None:
    row = MagicMock()
    row.proxy_wallet = "0xabc"
    row.type = "TRADE"
    row.timestamp = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    row.condition_id = "0xc"
    row.size = 10.0
    row.usdc_size = 5.5
    row.price = 0.55
    row.asset = "tok"
    row.side = "BUY"
    row.outcome_index = 0
    row.title = "Will X?"
    row.slug = "will-x"
    row.icon = ""
    row.event_slug = "ev"
    row.outcome = "Yes"
    row.name = "n"
    row.pseudonym = "p"
    row.bio = ""
    row.profile_image = ""
    row.profile_image_optimized = ""
    row.transaction_hash = "0xtx"
    mock_get_dc.return_value.get_activity.return_value = [row]

    out = fetchUserActivity("0xabc", limit=25, offset=5)

    mock_get_dc.return_value.get_activity.assert_called_once()
    ca = mock_get_dc.return_value.get_activity.call_args
    assert ca[1]["limit"] == 25
    assert ca[1]["offset"] == 5
    assert len(out) == 1
    assert out[0].wallet == "0xabc"
    assert out[0].type == "TRADE"
    assert out[0].market_slug == "will-x"


@patch("polymwk.users.activity.get_data_client")
def test_fetch_user_activity_clamps_limit(mock_get_dc) -> None:
    mock_get_dc.return_value.get_activity.return_value = []

    fetchUserActivity("0xabc", limit=9999)

    ca = mock_get_dc.return_value.get_activity.call_args
    assert ca[1]["limit"] == 500


@patch("polymwk.users.activity.get_data_client")
def test_fetch_user_activity_http_error(mock_get_dc) -> None:
    import httpx

    mock_get_dc.return_value.get_activity.side_effect = httpx.HTTPError("x")

    with pytest.raises(PolymwkApiError, match="activity"):
        fetchUserActivity("0x0000000000000000000000000000000000000002")
