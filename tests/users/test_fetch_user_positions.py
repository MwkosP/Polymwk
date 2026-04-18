"""Tests for :func:`~polymwk.users.positions.fetchUserPositions`."""

from unittest.mock import MagicMock, patch

import pytest

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.users.positions import fetchUserPositions


def test_fetch_user_positions_rejects_empty_user() -> None:
    with pytest.raises(PolymwkError, match="required"):
        fetchUserPositions("", limit=10)


@patch("polymwk.users.positions.get_data_client")
def test_fetch_user_positions_closed_maps_and_limits(mock_get_dc) -> None:
    from datetime import UTC, datetime

    row = MagicMock()
    row.proxy_wallet = "0xabc"
    row.slug = "closed-m"
    row.title = "Resolved?"
    row.outcome = "No"
    row.avg_price = 0.2
    row.current_price = 1.0
    row.total_bought = 50.0
    row.realized_pnl = 12.5
    row.timestamp = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
    row.condition_id = "0xcond"
    mock_get_dc.return_value.get_closed_positions.return_value = [row, row]

    out = fetchUserPositions("0xabc", limit=1, status="closed")

    mock_get_dc.return_value.get_closed_positions.assert_called_once()
    assert len(out) == 1
    c = out[0]
    assert c.wallet == "0xabc"
    assert c.market_slug == "closed-m"
    assert c.realized_pnl == 12.5
    assert c.condition_id == "0xcond"


@patch("polymwk.users.positions.get_data_client")
def test_fetch_user_positions_active_maps_rows(mock_get_dc) -> None:
    row = MagicMock()
    row.proxy_wallet = "0xabc"
    row.slug = "some-market"
    row.title = "Will it rain?"
    row.outcome = "Yes"
    row.size = 100.0
    row.avg_price = 0.4
    row.current_price = 0.55
    row.current_value = 55.0
    row.cash_pnl = 15.0
    row.realized_pnl = 0.0
    mock_get_dc.return_value.get_positions.return_value = [row]

    out = fetchUserPositions("0xabc", limit=25)

    mock_get_dc.return_value.get_positions.assert_called_once()
    call_kw = mock_get_dc.return_value.get_positions.call_args
    assert call_kw[0][0]  # EthAddress
    assert call_kw[1] == {"limit": 25}

    assert len(out) == 1
    p = out[0]
    assert p.wallet == "0xabc"
    assert p.market_slug == "some-market"
    assert p.market_title == "Will it rain?"
    assert p.outcome == "Yes"
    assert p.size == 100.0
    assert p.unrealised_pnl == 15.0


@patch("polymwk.users.positions.get_data_client")
def test_fetch_user_positions_http_error_wraps(mock_get_dc) -> None:
    import httpx

    mock_get_dc.return_value.get_positions.side_effect = httpx.HTTPError("x")

    with pytest.raises(PolymwkApiError, match="positions"):
        fetchUserPositions("0x0000000000000000000000000000000000000002")


@patch("polymwk.users.positions.get_data_client")
def test_fetch_user_positions_closed_http_error(mock_get_dc) -> None:
    import httpx

    mock_get_dc.return_value.get_closed_positions.side_effect = httpx.HTTPError("x")

    with pytest.raises(PolymwkApiError, match="closed-positions"):
        fetchUserPositions("0x0000000000000000000000000000000000000003", status="closed")
