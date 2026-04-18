"""All users’ positions in one market (Data API ``/v1/market-positions``)."""

from __future__ import annotations

from typing import Literal

import httpx

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Market, MarketUsersPositionsSnapshot
from polymwk._internal.data import get_v1_market_positions
from polymwk.events.utils import (
    gamma_condition_id_for_market_slug,
    market_users_positions_snapshot_from_v1,
)

MarketUsersPositionsStatus = Literal["OPEN", "CLOSED", "ALL"]
MarketUsersPositionsSortBy = Literal[
    "TOKENS",
    "CASH_PNL",
    "REALIZED_PNL",
    "TOTAL_PNL",
]


def fetchMarketUsersPositions(
    market: str | Market,
    *,
    event_slug: str = "",
    limit: int = 100,
    offset: int = 0,
    status: MarketUsersPositionsStatus = "OPEN",
    sort_by: MarketUsersPositionsSortBy = "TOTAL_PNL",
    sort_direction: Literal["ASC", "DESC"] = "DESC",
    user: str | None = None,
) -> MarketUsersPositionsSnapshot:
    """
    Load ranked **positions for every user** in one **market** (one condition).

    Uses ``GET /v1/market-positions`` (same data as the site’s per-outcome PnL
    lists). Pass a market **slug** string or :class:`~polymwk.models.Market`.

    ``limit`` applies **per outcome token** (Yes and No each get up to ``limit`` rows).
    Optional ``user`` filters to a single proxy wallet.
    """
    slug = market.slug.strip() if isinstance(market, Market) else str(market).strip()
    if not slug:
        raise PolymwkError("market slug required for fetchMarketUsersPositions")

    condition_id = gamma_condition_id_for_market_slug(slug)
    try:
        raw = get_v1_market_positions(
            condition_id,
            limit=limit,
            offset=offset,
            status=status,
            sort_by=sort_by,
            sort_direction=sort_direction,
            user=user,
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Data API /v1/market-positions request failed") from exc

    return market_users_positions_snapshot_from_v1(
        slug, condition_id, raw, event_slug=event_slug
    )
