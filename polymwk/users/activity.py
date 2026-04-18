"""User activity feed from the Data API (``GET /activity``)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import httpx
from polymarket_apis.types.common import EthAddress
from polymarket_apis.types.data_types import ActivityType

from polymwk.exceptions import PolymwkApiError
from polymwk.models import Activity
from polymwk._internal.data import get_data_client
from polymwk.users import utils as user_utils

# Matches upstream ``get_activity`` cap — one HTTP request, bounded payload.
_MAX_ACTIVITY_PAGE = 500


def fetchUserActivity(
    user: str,
    *,
    limit: int = 100,
    offset: int = 0,
    side: Literal["BUY", "SELL"] | None = None,
    buy_only: bool = False,
    sell_only: bool = False,
    outcome_filter: Literal["any", "yes", "no"] = "any",
    yes_only: bool = False,
    no_only: bool = False,
    condition_id: str | list[str] | None = None,
    event_id: str | int | list[str] | list[int] | None = None,
    activity_types: ActivityType | list[ActivityType] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[Activity]:
    """
    Load recent **on-chain activity** for a user (trades, merges, redeems, etc.).

    ``user`` is a proxy wallet ``0x…`` or a username / ``@handle`` (resolved like
    :func:`fetchUserInfo`).

    **Buy / sell (server-side)** — ``side='BUY'`` or ``'SELL'``, or ``buy_only=True`` /
    ``sell_only=True`` (mutually exclusive with a conflicting ``side=``).

    **Yes / No outcomes (client-side)** — after each page is fetched, rows are filtered
    when ``outcome_filter='yes'|'no'``, or ``yes_only=True`` / ``no_only=True``. Only
    matches labels **Yes** / **No** (case-insensitive); other outcome names are dropped
    when filtering.

    Optional **``condition_id``** / **``event_id``** / **``activity_types``** / **``start``**
    / **``end``** are passed to the Data API. At most **500** rows per request; use
    **``offset``** to page. If you use outcome filtering, request a larger **``limit``**
    if you need more matching rows per call.
    """
    if limit <= 0:
        return []

    eff_side = user_utils.resolve_buy_sell_side(
        side,
        buy_only=buy_only,
        sell_only=sell_only,
        caller="fetchUserActivity",
    )
    eff_outcome = user_utils.resolve_yes_no_outcome(
        outcome_filter,
        yes_only=yes_only,
        no_only=no_only,
        caller="fetchUserActivity",
    )

    proxy = user_utils.resolve_user_to_proxy_wallet(user)
    lim = min(limit, _MAX_ACTIVITY_PAGE)
    off = max(0, offset)

    dc = get_data_client()
    try:
        raw = dc.get_activity(
            EthAddress(proxy),
            limit=lim,
            offset=off,
            side=eff_side,
            condition_id=condition_id,
            event_id=event_id,
            type=activity_types,
            start=start,
            end=end,
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Data API /activity request failed") from exc

    rows = user_utils.activities_from_data_api(raw)
    if eff_outcome != "any":
        rows = [
            r
            for r in rows
            if user_utils.row_matches_outcome_filter(r.outcome, eff_outcome)
        ]
    return rows
