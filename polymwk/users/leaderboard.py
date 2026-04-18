"""User leaderboard: single-user rank (``lb-api``) and full table (Data API ``/v1/leaderboard``)."""

from __future__ import annotations

import httpx
from typing import Literal, cast

from polymarket_apis.types.common import EthAddress
from polymarket_apis.types.data_types import UserMetric as DataApiUserMetric

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import UserLeaderboardRank, UsersLeaderboardSnapshot
from polymwk._internal.data import get_data_client
from polymwk.users import utils as user_utils

UserLeaderboardMetric = Literal["profit", "volume"]
UserLeaderboardWindow = Literal["1d", "7d", "30d", "all"]

UsersLeaderboardTimeframe = Literal["today", "weekly", "monthly", "all"]
UsersLeaderboardCategory = Literal[
    "all",
    "politics",
    "sports",
    "crypto",
    "finance",
    "culture",
    "mentions",
    "weather",
    "economics",
    "tech",
]

_DATA_API_CATEGORIES = frozenset(
    {
        "OVERALL",
        "POLITICS",
        "SPORTS",
        "CRYPTO",
        "FINANCE",
        "CULTURE",
        "MENTIONS",
        "WEATHER",
        "ECONOMICS",
        "TECH",
    }
)

_DataApiLeaderboardCategory = Literal[
    "OVERALL",
    "POLITICS",
    "SPORTS",
    "CRYPTO",
    "FINANCE",
    "CULTURE",
    "MENTIONS",
    "WEATHER",
    "ECONOMICS",
    "TECH",
]

_CATEGORY_ALIASES: dict[str, tuple[str, str]] = {
    # slug → (Data API enum, short label for display)
    "all": ("OVERALL", "All categories"),
    "overall": ("OVERALL", "All categories"),
    "politics": ("POLITICS", "Politics"),
    "sports": ("SPORTS", "Sports"),
    "crypto": ("CRYPTO", "Crypto"),
    "finance": ("FINANCE", "Finance"),
    "culture": ("CULTURE", "Culture"),
    "mentions": ("MENTIONS", "Mentions"),
    "weather": ("WEATHER", "Weather"),
    "economics": ("ECONOMICS", "Economics"),
    "tech": ("TECH", "Tech"),
}

_TIMEFRAME_TO_API: dict[str, tuple[Literal["DAY", "WEEK", "MONTH", "ALL"], str]] = {
    "today": ("DAY", "Today"),
    "weekly": ("WEEK", "Weekly"),
    "monthly": ("MONTH", "Monthly"),
    "all": ("ALL", "All"),
}


def _resolve_leaderboard_category(category: str) -> tuple[str, str, str]:
    """
    Return ``(api_category, slug, display_label)``.

    Accepts UI-style slugs (``all``, ``politics``) or Data API names (``OVERALL``, ``POLITICS``).
    """
    raw = (category or "").strip()
    if not raw:
        raise PolymwkError("fetchUsersLeaderboard: category must not be empty")
    key = raw.lower()
    if key in _CATEGORY_ALIASES:
        api, label = _CATEGORY_ALIASES[key]
        slug = "all" if api == "OVERALL" else key
        return (api, slug, label)
    up = raw.upper()
    if up in _DATA_API_CATEGORIES:
        slug = "all" if up == "OVERALL" else up.lower()
        if slug in _CATEGORY_ALIASES:
            label = _CATEGORY_ALIASES[slug][1]
        else:
            label = up.title()
        return (up, slug, label)
    raise PolymwkError(
        f"fetchUsersLeaderboard: unknown category {raw!r} "
        f"(try 'all', 'politics', 'sports', … or OVERALL, POLITICS, …)"
    )


def fetchUserLeaderboardRank(
    user: str,
    *,
    metric: UserLeaderboardMetric = "profit",
    window: UserLeaderboardWindow = "all",
    include_cross_metric: bool = True,
) -> UserLeaderboardRank:
    """
    Load **leaderboard rank** for a user from ``lb-api`` (profit or volume, by window).

    ``user`` is a proxy wallet ``0x…`` or a username / ``@handle`` (resolved like
    :func:`fetchUserInfo`).

    When ``include_cross_metric`` is True (default), also calls ``get_user_metric``
    for the **other** metric in the same window (e.g. volume when ``metric='profit'``)
    so displays can show both numbers.
    """
    proxy = user_utils.resolve_user_to_proxy_wallet(user)
    addr = EthAddress(proxy)
    dc = get_data_client()

    try:
        rank_row = dc.get_leaderboard_user_rank(addr, metric=metric, window=window)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Leaderboard rank request failed") from exc

    other_row: DataApiUserMetric | None = None
    if include_cross_metric:
        cross: Literal["profit", "volume"] = "volume" if metric == "profit" else "profit"
        try:
            other_row = dc.get_user_metric(addr, metric=cross, window=window)
        except (httpx.HTTPError, IndexError, KeyError, ValueError, TypeError):
            other_row = None

    return user_utils.user_leaderboard_rank_from_lb_api(
        rank_row,
        metric=metric,
        window=window,
        other_metric_row=other_row,
    )


def fetchUsersLeaderboard(
    *,
    timeframe: UsersLeaderboardTimeframe = "today",
    category: str = "all",
    order_by: Literal["pnl", "vol"] = "pnl",
    limit: int = 25,
    offset: int = 0,
) -> UsersLeaderboardSnapshot:
    """
    Load the **public leaderboard** from the Data API (same data as the site UI).

    ``timeframe`` maps to Polymarket periods: today → DAY, weekly → WEEK,
    monthly → MONTH, all → ALL.

    ``category`` defaults to ``\"all\"`` (OVERALL). You can pass slugs such as
    ``\"politics\"``, ``\"sports\"``, ``\"crypto\"``, ``\"finance\"``, ``\"culture\"``,
    ``\"mentions\"``, ``\"weather\"``, ``\"economics\"``, ``\"tech\"``, or the API
    enum names (``\"POLITICS\"``, …).

    ``order_by`` controls sort order: ``\"pnl\"`` (profit/loss) or ``\"vol\"`` (volume).
    Each row still includes both PnL and volume.

    ``limit`` must be between 1 and 50; ``offset`` between 0 and 1000 (Data API rules).
    """
    if timeframe not in _TIMEFRAME_TO_API:
        raise PolymwkError(
            f"fetchUsersLeaderboard: unknown timeframe {timeframe!r} "
            f"(use 'today', 'weekly', 'monthly', 'all')"
        )
    if not 1 <= limit <= 50:
        raise PolymwkError("fetchUsersLeaderboard: limit must be between 1 and 50")
    if not 0 <= offset <= 1000:
        raise PolymwkError("fetchUsersLeaderboard: offset must be between 0 and 1000")

    api_cat, slug, cat_label = _resolve_leaderboard_category(category)
    time_period, _ = _TIMEFRAME_TO_API[timeframe]
    api_order: Literal["PNL", "VOL"] = "PNL" if order_by == "pnl" else "VOL"

    dc = get_data_client()
    try:
        rows = dc.get_leaderboard_rankings(
            category=cast(_DataApiLeaderboardCategory, api_cat),
            time_period=time_period,
            order_by=api_order,
            limit=limit,
            offset=offset,
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Leaderboard rankings request failed") from exc

    entries = [user_utils.leaderboard_entry_from_data_api(r) for r in rows]
    return UsersLeaderboardSnapshot(
        timeframe=timeframe,
        category=slug,
        category_label=cat_label,
        order_by=order_by,
        entries=entries,
    )
