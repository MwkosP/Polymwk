"""Top holders per market (Data API, condition-scoped)."""

from __future__ import annotations

import httpx

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Market, MarketTopHoldersSnapshot
from polymwk._internal.data import get_data_client
from polymwk.events.utils import (
    gamma_condition_id_for_market_slug,
    market_top_holders_snapshot_from_api,
)


def fetchMarketTopHolders(
    market: str | Market,
    *,
    limit: int = 100,
    min_balance: int = 1,
    event_slug: str = "",
) -> MarketTopHoldersSnapshot:
    """
    Load ranked holders for each **outcome token** of one **market** (one condition).

    The Data API keys holders by ``condition_id``, not by event slug. Pass a **market
    slug** string or a :class:`~polymwk.models.Market` (``slug`` is used).

    Optional ``event_slug`` is stored on the snapshot for display (e.g. under
    :func:`~polymwk.displays.events.market_holders.displayMarketTopHolders`).

    Returns one group per outcome token (typically Yes and No for binaries), each
    with a list of :class:`~polymwk.models.MarketTopHolder`.
    """
    slug = market.slug.strip() if isinstance(market, Market) else str(market).strip()
    if not slug:
        raise PolymwkError("market slug required for fetchMarketTopHolders")

    condition_id = gamma_condition_id_for_market_slug(slug)
    data = get_data_client()
    try:
        raw = data.get_holders(
            condition_id, limit=limit, min_balance=min_balance
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Data API /holders request failed") from exc

    return market_top_holders_snapshot_from_api(
        slug, condition_id, raw, event_slug=event_slug
    )
