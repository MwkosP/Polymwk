"""Gamma market resolution + UMA fields (what Polymarket exposes on the market object)."""

from __future__ import annotations

from datetime import datetime

import httpx

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Event, Market, MarketResolutionSnapshot
from polymwk._internal.gamma import get_gamma_client
from polymarket_apis.types.gamma_types import Event as GammaEvent
from polymarket_apis.types.gamma_types import GammaMarket


def _strip(v: object | None) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _as_datetime(v: object | None) -> datetime | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    return None


def _snapshot_from_gamma(
    gm: GammaMarket,
    *,
    requested_slug: str,
    event_slug: str,
    event_title: str,
    market_question_hint: str,
    ge: GammaEvent | None,
) -> MarketResolutionSnapshot:
    mslug = _strip(gm.slug) or _strip(gm.id) or requested_slug
    question = market_question_hint or _strip(gm.question)
    res_src = _strip(gm.resolution_source)
    if ge is not None and not res_src:
        res_src = _strip(ge.resolution_source)

    cid = _strip(gm.condition_id)
    qid = _strip(gm.question_id)
    rb = _strip(gm.resolved_by)

    return MarketResolutionSnapshot(
        market_slug=mslug,
        market_question=question,
        event_slug=event_slug,
        event_title=event_title,
        condition_id=cid,
        question_id=qid,
        resolution_source=res_src,
        closed=gm.closed,
        archived=gm.archived,
        active=gm.active,
        closed_time=_strip(gm.closed_time),
        resolved_by=rb,
        uma_resolution_status=_strip(gm.uma_resolution_status) or None,
        uma_end_date=_as_datetime(gm.uma_end_date),
        uma_end_date_iso=_as_datetime(gm.uma_end_date_iso),
        uma_bond=_strip(gm.uma_bond),
        uma_reward=_strip(gm.uma_reward),
    )


def fetchMarketResolution(
    market: str | Market,
    *,
    event_slug: str = "",
    event_title: str = "",
    merge_event_resolution_source: bool = True,
) -> MarketResolutionSnapshot:
    """
    Load **resolution-related fields** Gamma attaches to a market (UMA dates/status,
    ``closed`` / ``resolvedBy``, ``conditionId``, optional ``resolutionSource``).

    When ``merge_event_resolution_source`` is True and ``event_slug`` is set, loads the
    event and uses its ``resolutionSource`` if the market’s is empty.
    """
    if isinstance(market, Market):
        slug = market.slug.strip()
        q_hint = (market.question or "").strip()
    else:
        slug = str(market).strip()
        q_hint = ""
    if not slug:
        raise PolymwkError("market slug required for fetchMarketResolution")

    client = get_gamma_client()
    try:
        gm = client.get_market_by_slug(slug)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma market-by-slug request failed") from exc

    ge: GammaEvent | None = None
    es = event_slug.strip()
    if merge_event_resolution_source and es:
        try:
            ge = client.get_event_by_slug(es)
        except httpx.HTTPError:
            ge = None

    return _snapshot_from_gamma(
        gm,
        requested_slug=slug,
        event_slug=es,
        event_title=event_title.strip(),
        market_question_hint=q_hint,
        ge=ge,
    )


def fetchEventResolution(
    event: Event,
    *,
    market_index: int = 0,
    merge_event_resolution_source: bool = True,
) -> MarketResolutionSnapshot:
    """
    Same as :func:`fetchMarketResolution` for one market on an :class:`~polymwk.models.Event`.
    """
    if not event.markets:
        raise PolymwkError("event has no markets for fetchEventResolution")
    if market_index < 0 or market_index >= len(event.markets):
        raise PolymwkError("market_index out of range for fetchEventResolution")
    m = event.markets[market_index]
    return fetchMarketResolution(
        m,
        event_slug=event.slug,
        event_title=event.title,
        merge_event_resolution_source=merge_event_resolution_source,
    )
