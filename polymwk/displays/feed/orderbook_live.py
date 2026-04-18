"""Live terminal order book: same ladder as :func:`~polymwk.displays.events.orderbook.displayOrderBook`, WebSocket-driven."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.displays.events.orderbook import displayOrderBook
from polymwk.displays.utils import term_style
from polymwk.feed.orderbook import subscribeMarketOrderBook
from polymwk.models import OrderBook, OrderBookUpdate


def merge_order_book_with_bba(book: OrderBook, u: OrderBookUpdate) -> OrderBook:
    """Apply a ``best_bid_ask`` tick onto the last full snapshot (depth rows unchanged)."""
    bb = book.best_bid if u.best_bid is None else u.best_bid
    ba = book.best_ask if u.best_ask is None else u.best_ask
    spread = max(0.0, ba - bb)
    midpoint = (bb + ba) / 2.0
    ts = u.timestamp if u.timestamp is not None else book.timestamp
    return book.model_copy(
        update={
            "best_bid": bb,
            "best_ask": ba,
            "spread": spread,
            "midpoint": midpoint,
            "timestamp": ts,
        }
    )


def displayLiveOrderBook(
    token_id: str,
    *,
    market_slug: str | None = None,
    event_slug: str = "",
    market_question: str = "",
    header_subtitle: str | None = None,
    max_levels: int = 12,
    bar_width: int | None = None,
    custom_feature_enabled: bool = True,
    stream: TextIO | None = None,
) -> None:
    """
    Subscribe to the CLOB market WebSocket and **redraw** the order book on each update.

    Uses the same boxed header and depth ladder as :func:`~polymwk.displays.events.orderbook.displayOrderBook`.
    The screen is cleared before each draw (ANSI). **Blocks** until the connection ends; use **Ctrl+C**
    to stop. Until the first full ``book`` message arrives, shows a short waiting line.
    """
    out = stream if stream is not None else sys.stdout
    _bold, dim, _accent, rst = term_style(out)
    state: list[OrderBook | None] = [None]

    def redraw() -> None:
        out.write("\033[2J\033[H")
        if state[0] is None:
            out.write(f"{dim}Waiting for first order book snapshot…{rst}\n")
            out.flush()
            return
        displayOrderBook(
            state[0],
            stream=out,
            max_levels=max_levels,
            bar_width=bar_width,
            event_slug=event_slug,
            market_question=market_question,
            header_subtitle=header_subtitle,
        )
        out.write(f"{dim}Live WebSocket · Ctrl+C to stop{rst}\n")
        out.flush()

    def on_order_book(ob: OrderBook) -> None:
        state[0] = ob
        redraw()

    def on_best_bid_ask(u: OrderBookUpdate) -> None:
        if state[0] is not None:
            state[0] = merge_order_book_with_bba(state[0], u)
            redraw()

    redraw()
    subscribeMarketOrderBook(
        token_id,
        market_slug=market_slug,
        custom_feature_enabled=custom_feature_enabled,
        on_order_book=on_order_book,
        on_best_bid_ask=on_best_bid_ask,
    )
