"""Print a CLOB order book snapshot (exchange-style depth ladder)."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import BookLevel, OrderBook
from polymwk.displays.utils import (
    center_line,
    content_width,
    emit_order_book_menu_header,
    exchange_depth_colors,
    format_depth_bar,
    format_display_num,
    term_style,
    term_width,
)


def displayOrderBook(
    book: OrderBook,
    *,
    stream: TextIO | None = None,
    max_levels: int = 12,
    bar_width: int | None = None,
    event_slug: str = "",
    market_question: str = "",
    header_subtitle: str | None = None,
) -> None:
    """
    Pretty-print an :class:`~polymwk.models.OrderBook` like a typical crypto ladder.

    Header matches :func:`~polymwk.displays.events.listing.displayEvents` (boxed title).
    Pass ``event_slug`` and ``market_question`` for left ``Event:`` / ``Market:``
    lines under the box.

    **Asks (sell / red)** above the middle: highest price at the top, **best ask**
    directly under the mid band (Binance-style).

    **Bids (buy / green)** below: **best bid** directly under the mid band, then
    lower bids downward.

    ``header_subtitle`` defaults to the book’s ``market_slug`` (centered under
    “Order book”), like “Events for bitcoin” under “Display”.
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(book, OrderBook):
        raise PolymwkError("displayOrderBook expects polymwk.models.OrderBook")

    bold, dim, accent, rst = term_style(out)
    bid_c, ask_c, bar_bid, bar_ask, xrst = exchange_depth_colors(out)
    term_w = term_width(out)
    inner_w = content_width(stream)

    slug = book.market_slug or ""
    subtitle = header_subtitle if header_subtitle is not None else slug or "Market"
    market_left = market_question.strip() or slug or "—"

    emit_order_book_menu_header(
        out,
        subtitle=subtitle,
        event_slug=event_slug.strip() or "—",
        market_line=market_left,
        bold=bold,
        dim=dim,
        accent=accent,
        rst=rst,
        term_w=term_w,
    )
    out.write(f"  {dim}{book.timestamp.isoformat()}{rst}\n\n")

    raw_asks = list(book.asks or [])
    raw_bids = list(book.bids or [])
    asks_near = sorted(raw_asks, key=lambda lv: lv.price)[:max_levels]
    bids_near = sorted(raw_bids, key=lambda lv: lv.price, reverse=True)[:max_levels]
    asks_display = sorted(asks_near, key=lambda lv: lv.price, reverse=True)
    bids_display = bids_near

    max_ask_sz = max((lv.size for lv in asks_display), default=0.0) or 1.0
    max_bid_sz = max((lv.size for lv in bids_display), default=0.0) or 1.0

    bw = bar_width
    if bw is None:
        bw = max(8, min(22, inner_w - 28))
    bw = max(4, bw)

    def _row_side(lv: BookLevel, *, side: str) -> str:
        cap = max_ask_sz if side == "ask" else max_bid_sz
        bar_raw = format_depth_bar(lv.size, cap, bw)
        ac = ask_c if side == "ask" else bid_c
        bc = bar_ask if side == "ask" else bar_bid
        price_s = f"{lv.price:.4f}"
        size_s = format_display_num(lv.size)
        return (
            f"  {ac}{price_s:>8}{xrst}  "
            f"{ac}{size_s:>12}{xrst}  "
            f"{bc}{bar_raw}{xrst}"
        )

    out.write(f"  {dim}ASKS (sell){rst}\n")
    if asks_display:
        for lv in asks_display:
            out.write(_row_side(lv, side="ask") + "\n")
    else:
        out.write(f"  {dim}(no asks){rst}\n")

    mid_line = (
        f"{dim}──{rst} {bold}mid {book.midpoint:.4f}{rst} {dim}·{rst} "
        f"{dim}spread {book.spread:.4f}{rst} {dim}·{rst} "
        f"{dim}bid {book.best_bid:.4f}{rst} {dim}/{rst} "
        f"{dim}ask {book.best_ask:.4f}{rst} {dim}──{rst}"
    )
    center_line(out, mid_line, term_w)

    out.write(f"  {dim}BIDS (buy){rst}\n")
    if bids_display:
        for lv in bids_display:
            out.write(_row_side(lv, side="bid") + "\n")
    else:
        out.write(f"  {dim}(no bids){rst}\n")

    out.write("\n")
