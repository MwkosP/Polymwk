"""Discover Gamma series that appear under tag-filtered events."""

from __future__ import annotations

from collections.abc import Sequence

import httpx

from polymwk.constants import DEFAULT_EVENT_LIMIT
from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Series
from polymwk._internal.gamma import get_gamma_client
from polymwk._internal.gamma_convert import _float_val
from polymwk.events.utils import (
    EventFetchStatus,
    apply_series_fetch_flags,
    collect_series_from_tagged_gamma_events,
    event_status_to_gamma_params,
    fetch_raw_gamma_events_by_tags,
    gamma_series_to_polymwk,
    parse_serie_lookup,
)
from polymwk.utils.event_query import normalize_event_tag_query


def fetchSerie(
    slug: str | None = None,
    *,
    id: str | None = None,
    show_vol: bool = True,
) -> Series:
    """
    Load a **single** series by **slug** (default) or Gamma **id**.

    ``fetchSerie("fed-rate-decisions")`` — slug as first argument.

    ``fetchSerie(id="42")`` — internal series id.
    """
    kind, value = parse_serie_lookup(slug, id)
    client = get_gamma_client()
    try:
        if kind == "slug":
            part = client.get_series(limit=1, slug=value)
            if not part:
                raise PolymwkError(f"no series for slug={value!r}")
            raw = part[0]
        else:
            raw = client.get_series_by_id(value)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma series request failed") from exc

    out = gamma_series_to_polymwk(raw, event_count=0)
    return apply_series_fetch_flags(out, show_vol=show_vol)


def fetchSeries(
    query: str | Sequence[str],
    *,
    limit: int | None = None,
    status: EventFetchStatus | None = "active",
    show_vol: bool = True,
    event_scan_limit: int | None = None,
) -> list[Series]:
    """
    Return **distinct** series tied to events that match the same tag ``query`` as :func:`~polymwk.events.fetch.fetchEvents`.

    Gamma does not expose tag filters on ``/series``; polymwk discovers series by scanning
    tag-matched **events**, reading embedded ``series`` payloads (and resolving ``seriesSlug``
    via ``get_series`` when needed), de-duplicating, sorting by **volume**, then taking
    ``limit`` rows.

    ``event_scan_limit`` caps how many events are pulled from Gamma for this scan (default
    ``min(500, max(80, (limit or 20) * 25))``). Raise it if you need more coverage.
    """
    tags = normalize_event_tag_query(query)
    if not tags:
        raise PolymwkError("query must contain at least one non-empty tag string")

    cap = limit if limit is not None else DEFAULT_EVENT_LIMIT
    if cap < 1:
        raise PolymwkError("limit must be >= 1")

    scan = event_scan_limit
    if scan is None:
        scan = min(500, max(80, cap * 25))
    if scan < 1:
        raise PolymwkError("event_scan_limit must be >= 1")

    filters = event_status_to_gamma_params(status)
    client = get_gamma_client()
    raw = fetch_raw_gamma_events_by_tags(client, tags, scan, filters)

    pairs = collect_series_from_tagged_gamma_events(
        client, raw, status=status
    )
    pairs.sort(key=lambda t: _float_val(t[0].volume), reverse=True)
    out = [
        gamma_series_to_polymwk(gs, event_count=c) for gs, c in pairs[:cap]
    ]
    return [apply_series_fetch_flags(s, show_vol=show_vol) for s in out]
