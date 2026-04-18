"""Fetch markets by slug, id, condition_id, or token_id (Gamma + CLOB)."""

from __future__ import annotations

import httpx

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Event, Market
from polymwk._internal.gamma import get_gamma_client
from polymwk._internal.gamma_convert import (
    _clob_yes_token_id,
    _fetch_clob_mid_cache,
    gamma_market_to_polymwk,
)
from polymwk.events.fetch import fetchEvent
from polymwk.events.utils import parse_market_lookup


def fetchMarket(
    slug: str | None = None,
    *,
    id: str | None = None,
    condition_id: str | None = None,
    token_id: str | None = None,
    show_vol: bool = True,
) -> Market:
    """
    Load a **single** market.

    **Default — slug** (from the Polymarket URL path after the event slug):

    ``fetchMarket("will-btc-hit-100k-2025")``

    **By Gamma internal id:** ``fetchMarket(id="253591")``

    **By condition id** (Data API): ``fetchMarket(condition_id="0x...")``

    **By outcome token id** (CLOB): ``fetchMarket(token_id="21742633143...")``

    Pass **exactly one** identifier.
    """
    kind, value = parse_market_lookup(slug, id, condition_id, token_id)
    client = get_gamma_client()
    try:
        if kind == "slug":
            raw = client.get_market_by_slug(value)
        elif kind == "id":
            raw = client.get_market_by_id(value)
        elif kind == "condition_id":
            part = client.get_markets(condition_ids=[value], limit=1)
            if not part:
                raise PolymwkError(f"no market for condition_id={value!r}")
            raw = part[0]
        else:
            part = client.get_markets(token_ids=[value], limit=1)
            if not part:
                raise PolymwkError(f"no market for token_id={value!r}")
            raw = part[0]
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma market request failed") from exc

    tid = _clob_yes_token_id(raw)
    mids: dict[str, float] = {}
    if tid:
        mids = _fetch_clob_mid_cache([tid])
    yes = mids.get(tid) if tid else None
    m = gamma_market_to_polymwk(raw, yes_from_clob=yes)
    if not show_vol:
        return m.model_copy(
            update={"volume": 0.0, "volume_24h": None, "liquidity": 0.0}
        )
    return m


def fetchMarkets(
    event: str | Event,
) -> list[Market]:
    """
    Return all markets for an event.

    ``event`` is an :class:`~polymwk.models.Event` or an event **slug** string.

    If the event was loaded with ``get_markets=False``, this refetches the event by slug.
    """
    if isinstance(event, Event):
        if event.markets:
            return list(event.markets)
        s = (event.slug or "").strip()
        if not s:
            raise PolymwkError("Event has no slug; cannot load markets")
        ev = fetchEvent(s)
        return list(ev.markets)
    slug = str(event).strip()
    if not slug:
        raise PolymwkError("event slug must be non-empty")
    return list(fetchEvent(slug).markets)
