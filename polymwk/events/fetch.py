"""Fetch events from Gamma by tag slug(s)."""

from __future__ import annotations

from collections.abc import Sequence

import httpx

from polymwk.constants import DEFAULT_EVENT_LIMIT
from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Event
from polymwk._internal.gamma import get_gamma_client
from polymwk._internal.gamma_convert import (
    gamma_event_to_polymwk,
    prefetch_clob_mids_for_gamma_events,
)
from polymwk.events.utils import (
    EventFetchStatus,
    apply_event_fetch_flags,
    event_status_to_gamma_params,
    fetch_raw_gamma_events_by_tags,
    parse_event_lookup,
)
from polymwk.utils.event_query import normalize_event_tag_query


def fetchEvent(
    slug: str | None = None,
    *,
    id: str | None = None,
    get_markets: bool = True,
    show_vol: bool = True,
    only_open_markets: bool = True,
) -> Event:
    """
    Load a **single** event by **slug** (default — copy from the Polymarket URL) or by Gamma **id**.

    ``fetchEvent("fed-decision-in-october")`` — slug as first argument.

    ``fetchEvent(id="16085")`` — internal event id.

    ``only_open_markets`` mirrors :func:`fetchEvents` with ``status="active"``: when True, resolved /
    inactive markets are omitted from :attr:`~polymwk.models.Event.markets`.
    """
    kind, value = parse_event_lookup(slug, id)
    client = get_gamma_client()
    try:
        if kind == "slug":
            raw = client.get_event_by_slug(value)
        else:
            raw = client.get_event_by_id(value)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma event request failed") from exc

    only_open = only_open_markets
    shared_mids = prefetch_clob_mids_for_gamma_events([raw], only_open_markets=only_open)
    ev = gamma_event_to_polymwk(
        raw, only_open_markets=only_open, clob_mid_cache=shared_mids
    )
    return apply_event_fetch_flags(ev, show_vol=show_vol, get_markets=get_markets)


def fetchEvents(
    query: str | Sequence[str],
    *,
    limit: int | None = None,
    status: EventFetchStatus | None = "active",
    show_vol: bool = True,
    get_markets: bool = True,
) -> list[Event]:
    """
    Load events whose tags match the given slug(s).

    ``query`` is a single tag slug string (e.g. ``\"bitcoin\"``) or a list of slugs;
    results are merged and de-duplicated by event id, then truncated to ``limit``.

    When ``get_markets`` is False, each event omits the ``markets`` list (but keeps
    ``market_count`` and ``primary_yes_price`` / ``primary_no_price``). Use
    :func:`~polymwk.events.markets.fetchMarkets` later to load markets for a known event.
    When ``show_vol`` is False, event and market volumes are zeroed.

    With the default ``status="active"``, **closed / inactive markets are dropped**
    from each event so lists match the tradeable outcomes on the site (resolved
    rows at 0%/100% no longer crowd out live markets).
    """
    tags = normalize_event_tag_query(query)
    if not tags:
        raise PolymwkError("query must contain at least one non-empty tag string")

    cap = limit if limit is not None else DEFAULT_EVENT_LIMIT
    if cap < 1:
        raise PolymwkError("limit must be >= 1")

    filters = event_status_to_gamma_params(status)
    client = get_gamma_client()
    raw = fetch_raw_gamma_events_by_tags(client, tags, cap, filters)

    only_open = status == "active"
    shared_mids = prefetch_clob_mids_for_gamma_events(
        raw, only_open_markets=only_open
    )
    out = [
        gamma_event_to_polymwk(
            e, only_open_markets=only_open, clob_mid_cache=shared_mids
        )
        for e in raw
    ]
    return [
        apply_event_fetch_flags(ev, show_vol=show_vol, get_markets=get_markets)
        for ev in out
    ]
