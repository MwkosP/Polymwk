"""``displayLiveOrderBook`` wiring."""

from __future__ import annotations

from datetime import UTC, datetime
from io import StringIO
from unittest.mock import patch

from polymwk.displays.feed.orderbook_live import displayLiveOrderBook, merge_order_book_with_bba
from polymwk.models import BookLevel, OrderBook, OrderBookUpdate


def test_merge_order_book_with_bba_updates_top() -> None:
    ts = datetime.now(UTC)
    book = OrderBook(
        market_slug="m",
        best_bid=0.4,
        best_ask=0.6,
        spread=0.2,
        midpoint=0.5,
        bids=[BookLevel(price=0.4, size=10.0)],
        asks=[BookLevel(price=0.6, size=5.0)],
        timestamp=ts,
    )
    u = OrderBookUpdate(market_slug="m", best_bid=0.41, best_ask=0.59, timestamp=ts)
    out = merge_order_book_with_bba(book, u)
    assert out.best_bid == 0.41
    assert out.best_ask == 0.59
    assert out.spread == 0.18
    assert abs(out.midpoint - 0.5) < 1e-9
    assert out.bids == book.bids
    assert out.asks == book.asks


@patch("polymwk.displays.feed.orderbook_live.subscribeMarketOrderBook")
def test_display_live_order_book_passes_token_to_subscribe(mock_sub) -> None:
    mock_sub.side_effect = lambda *a, **k: None
    out = StringIO()
    displayLiveOrderBook("tid", market_slug="slug", stream=out)
    mock_sub.assert_called_once()
    assert mock_sub.call_args[0][0] == "tid"
    assert mock_sub.call_args[1]["market_slug"] == "slug"
    assert callable(mock_sub.call_args[1]["on_order_book"])
    assert callable(mock_sub.call_args[1]["on_best_bid_ask"])
