"""Gamma market (and optional event) text: rules, resolution source."""

from __future__ import annotations

import httpx

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Event, Market, MarketRulesSnapshot
from polymwk._internal.gamma import get_gamma_client
from polymarket_apis.types.gamma_types import Event as GammaEvent
from polymarket_apis.types.gamma_types import GammaMarket


def _strip(v: object | None) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _snapshot_from_gamma(
    gm: GammaMarket,
    *,
    requested_slug: str,
    event_slug: str,
    event_title: str,
    market_question_hint: str,
    ge: GammaEvent | None,
    include_event_description: bool,
) -> MarketRulesSnapshot:
    mslug = _strip(gm.slug) or _strip(gm.id) or requested_slug
    question = market_question_hint or _strip(gm.question)
    rules_body = _strip(gm.description)
    res_src = _strip(gm.resolution_source)
    uma = _strip(gm.uma_resolution_status) or None

    event_description = ""
    if ge is not None:
        if not res_src:
            res_src = _strip(ge.resolution_source)
        if include_event_description:
            ed = _strip(ge.description)
            if ed and ed != rules_body:
                event_description = ed

    return MarketRulesSnapshot(
        market_slug=mslug,
        market_question=question,
        event_slug=event_slug,
        event_title=event_title,
        rules_body=rules_body,
        event_description=event_description,
        resolution_source=res_src,
        uma_resolution_status=uma,
    )


def fetchMarketRules(
    market: str | Market,
    *,
    event_slug: str = "",
    event_title: str = "",
    include_event_description: bool = True,
) -> MarketRulesSnapshot:
    """
    Load **rules / description** text for one market from Gamma (same slug path as
    ``fetchMarketPrices`` when given a slug).

    Pulls the market’s ``description`` (on-site “Rules” body) and
    ``resolution_source``; optionally loads the parent **event** by ``event_slug``
    to fill a missing resolution source and to attach a separate **event**
    description when it differs from the market text.
    """
    if isinstance(market, Market):
        slug = market.slug.strip()
        q_hint = (market.question or "").strip()
    else:
        slug = str(market).strip()
        q_hint = ""
    if not slug:
        raise PolymwkError("market slug required for fetchMarketRules")

    client = get_gamma_client()
    try:
        gm = client.get_market_by_slug(slug)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma market-by-slug request failed") from exc

    ge: GammaEvent | None = None
    es = event_slug.strip()
    if es:
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
        include_event_description=include_event_description,
    )


def fetchEventRules(
    event: Event,
    *,
    market_index: int = 0,
    include_event_description: bool = True,
) -> MarketRulesSnapshot:
    """
    Same as :func:`fetchMarketRules` for **one market** on an :class:`~polymwk.models.Event`
    (default: first market), passing ``event_slug`` / ``event_title`` for context.
    """
    if not event.markets:
        raise PolymwkError("event has no markets for fetchEventRules")
    if market_index < 0 or market_index >= len(event.markets):
        raise PolymwkError("market_index out of range for fetchEventRules")
    m = event.markets[market_index]
    return fetchMarketRules(
        m,
        event_slug=event.slug,
        event_title=event.title,
        include_event_description=include_event_description,
    )
