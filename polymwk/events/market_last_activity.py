"""Latest taker trades for one market (Data API ``/trades``)."""

from __future__ import annotations

import httpx

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Market, MarketLastActivitySnapshot
from polymwk._internal.data import get_data_client
from polymwk.events.utils import (
    gamma_condition_id_for_market_slug,
    market_last_activity_snapshot_from_trades,
)


def fetchMarketLastActivity(
    market: str | Market,
    *,
    limit: int = 50,
    offset: int = 0,
    event_slug: str = "",
    taker_only: bool = True,
) -> MarketLastActivitySnapshot:
    """
    Load the **newest** taker trades for one **market** (one condition), oldest last.

    Uses ``GET /trades`` with ``market=<condition_id>``. ``limit`` is capped at 500.
    """
    slug = market.slug.strip() if isinstance(market, Market) else str(market).strip()
    if not slug:
        raise PolymwkError("market slug required for fetchMarketLastActivity")

    condition_id = gamma_condition_id_for_market_slug(slug)
    data = get_data_client()
    try:
        raw = data.get_trades(
            limit=limit,
            offset=offset,
            condition_id=condition_id,
            taker_only=taker_only,
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Data API /trades request failed") from exc

    return market_last_activity_snapshot_from_trades(
        slug, condition_id, raw, event_slug=event_slug
    )
