"""Feed-only helpers (vendor WS shapes → ``polymwk.models``)."""

from __future__ import annotations

from polymarket_apis.types.websockets_types import BestBidAskEvent

from polymwk.models import OrderBookUpdate


def order_book_update_from_best_bid_ask(
    ev: BestBidAskEvent,
    *,
    market_slug: str,
) -> OrderBookUpdate:
    return OrderBookUpdate(
        market_slug=market_slug,
        best_bid=ev.best_bid,
        best_ask=ev.best_ask,
        timestamp=ev.timestamp,
    )
