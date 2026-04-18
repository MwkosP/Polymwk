"""Fetch a CLOB order book for one outcome token (REST snapshot)."""

from __future__ import annotations

import httpx

from polymwk.exceptions import PolymwkApiError
from polymwk.models import OrderBook
from polymwk._internal.clob import get_clob_client
from polymwk.events.utils import order_book_from_clob_summary


def fetchOrderBook(
    token_id: str,
    *,
    market_slug: str | None = None,
) -> OrderBook:
    """
    Load the current order book for a single **outcome token**.

    Polymarket’s CLOB is keyed by ``token_id`` (the ERC-1155 outcome asset), not by
    event slug. For a binary market, the first Gamma ``clobTokenIds`` entry is
    usually the **Yes** token; the second is **No** — each has its own book.

    ``market_slug`` is optional. When omitted, a follow-up CLOB ``get_market`` call
    resolves the slug from the book’s condition id for :attr:`~polymwk.models.OrderBook.market_slug`.
    """
    clob = get_clob_client()
    try:
        summary = clob.get_order_book(token_id)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("CLOB order book request failed") from exc

    slug = market_slug
    if slug is None:
        try:
            meta = clob.get_market(summary.condition_id)
            slug = meta.market_slug or ""
        except httpx.HTTPError:
            slug = ""

    return order_book_from_clob_summary(summary, market_slug=slug)
