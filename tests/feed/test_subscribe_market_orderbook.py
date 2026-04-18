"""``subscribeMarketOrderBook`` validation."""

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.feed.orderbook import subscribeMarketOrderBook


def test_subscribe_market_order_book_requires_callback() -> None:
    with pytest.raises(PolymwkError, match="on_order_book or on_best_bid_ask"):
        subscribeMarketOrderBook("123")
