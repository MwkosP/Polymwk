"""Subscribe to CLOB market WebSocket order-book streams for one outcome token."""

from __future__ import annotations

import httpx
from collections.abc import Callable

from lomond.events import Text
from polymarket_apis.clients.websockets_client import parse_market_event
from polymarket_apis.types.websockets_types import BestBidAskEvent, OrderBookSummaryEvent

from polymwk.events.utils import order_book_from_clob_summary
from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import OrderBook, OrderBookUpdate
from polymwk._internal.clob import get_clob_client
from polymwk._internal.websockets import get_polymarket_websockets_client
from polymwk.feed.utils import order_book_update_from_best_bid_ask


def subscribeMarketOrderBook(
    token_id: str,
    *,
    market_slug: str | None = None,
    custom_feature_enabled: bool = True,
    on_order_book: Callable[[OrderBook], None] | None = None,
    on_best_bid_ask: Callable[[OrderBookUpdate], None] | None = None,
) -> None:
    """
    Stream order-book updates for a single **outcome** ``token_id`` over the CLOB market WebSocket.

    Same token semantics as :func:`~polymwk.events.fetchOrderBook`. This call **blocks** until the
    connection ends (reconnects are handled by the underlying client).

    At least one of ``on_order_book`` or ``on_best_bid_ask`` must be provided. Full snapshots are
    delivered as :class:`~polymwk.models.OrderBook` (``event_type == "book"``). When
    ``custom_feature_enabled`` is true, ``best_bid_ask`` ticks are mapped to
    :class:`~polymwk.models.OrderBookUpdate`.

    ``market_slug`` is optional; when omitted, it is resolved once from the CLOB using the book’s
    ``condition_id`` (same idea as :func:`~polymwk.events.fetchOrderBook`).
    """
    if on_order_book is None and on_best_bid_ask is None:
        raise PolymwkError(
            "subscribeMarketOrderBook requires at least one of on_order_book or on_best_bid_ask"
        )

    slug_resolved: str | None = market_slug

    def _slug_for(condition_id: str) -> str:
        nonlocal slug_resolved
        if slug_resolved is not None:
            return slug_resolved
        clob = get_clob_client()
        try:
            meta = clob.get_market(condition_id)
            slug_resolved = meta.market_slug or ""
        except httpx.HTTPError:
            slug_resolved = ""
        return slug_resolved

    def _emit_book(ev: OrderBookSummaryEvent) -> None:
        if on_order_book is None or ev.token_id != token_id:
            return
        cid = str(ev.condition_id)
        slug = _slug_for(cid)
        on_order_book(order_book_from_clob_summary(ev, market_slug=slug))

    def process_event(text: Text) -> None:
        parsed = parse_market_event(text)
        if parsed is None:
            return
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, OrderBookSummaryEvent):
                    _emit_book(item)
            return
        if isinstance(parsed, OrderBookSummaryEvent):
            _emit_book(parsed)
            return
        if isinstance(parsed, BestBidAskEvent):
            if on_best_bid_ask is None or parsed.token_id != token_id:
                return
            slug = _slug_for(str(parsed.condition_id))
            on_best_bid_ask(order_book_update_from_best_bid_ask(parsed, market_slug=slug))

    client = get_polymarket_websockets_client()
    try:
        client.market_socket(
            [token_id],
            custom_feature_enabled=custom_feature_enabled,
            process_event=process_event,
        )
    except Exception as exc:
        raise PolymwkApiError("CLOB market WebSocket connection failed") from exc
