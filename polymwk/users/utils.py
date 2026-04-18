"""User domain helpers (handle resolution, Gamma profile → :class:`~polymwk.models.UserInfo`, Data API stats)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import httpx
from polymarket_apis.types.common import EthAddress
from polymarket_apis.types.data_types import Activity as DataApiActivity
from polymarket_apis.types.data_types import ActivityType
from polymarket_apis.types.data_types import ClosedPosition as DataApiClosedPosition
from polymarket_apis.types.data_types import Position as DataApiOpenPosition
from polymarket_apis.types.data_types import Trade as DataApiTrade
from polymarket_apis.types.data_types import UserMetric as DataApiUserMetric
from polymarket_apis.types.data_types import UserProfile
from polymarket_apis.types.data_types import LeaderboardUser as DataApiLeaderboardUser
from polymarket_apis.types.data_types import UserRank as DataApiUserRank

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import (
    Activity,
    LeaderboardEntry,
    Position,
    Trade,
    UserClosedPosition,
    UserIdentity,
    UserInfo,
    UserLeaderboardRank,
)
from polymwk._internal.data import get_data_client
from polymwk._internal.gamma import get_gamma_client

_HEX_PREFIX = "0x"
_PROXY_WALLET_HEX_LEN = 42

UserOutcomeFilter = Literal["any", "yes", "no"]


def resolve_buy_sell_side(
    side: Literal["BUY", "SELL"] | None,
    *,
    buy_only: bool,
    sell_only: bool,
    caller: str,
) -> Literal["BUY", "SELL"] | None:
    """Merge ``side=`` with ``buy_only`` / ``sell_only`` flags (for activity/trades)."""
    if buy_only and sell_only:
        raise PolymwkError(f"{caller}: buy_only and sell_only cannot both be True")
    if buy_only:
        if side is not None and side != "BUY":
            raise PolymwkError(f"{caller}: buy_only conflicts with side={side!r}")
        return "BUY"
    if sell_only:
        if side is not None and side != "SELL":
            raise PolymwkError(f"{caller}: sell_only conflicts with side={side!r}")
        return "SELL"
    return side


def resolve_yes_no_outcome(
    outcome_filter: UserOutcomeFilter,
    *,
    yes_only: bool,
    no_only: bool,
    caller: str,
) -> UserOutcomeFilter:
    """Merge ``outcome_filter`` with ``yes_only`` / ``no_only`` (client-side row filter)."""
    if yes_only and no_only:
        raise PolymwkError(f"{caller}: yes_only and no_only cannot both be True")
    if yes_only:
        if outcome_filter not in ("any", "yes"):
            raise PolymwkError(
                f"{caller}: yes_only conflicts with outcome_filter={outcome_filter!r}"
            )
        return "yes"
    if no_only:
        if outcome_filter not in ("any", "no"):
            raise PolymwkError(
                f"{caller}: no_only conflicts with outcome_filter={outcome_filter!r}"
            )
        return "no"
    return outcome_filter


def row_matches_outcome_filter(outcome: str, outcome_filter: UserOutcomeFilter) -> bool:
    """Binary markets: outcome label ``Yes`` / ``No`` (case-insensitive)."""
    if outcome_filter == "any":
        return True
    o = (outcome or "").strip().casefold()
    if outcome_filter == "yes":
        return o == "yes"
    if outcome_filter == "no":
        return o == "no"
    return True


def is_proxy_wallet_address(s: str) -> bool:
    t = s.strip()
    if len(t) != _PROXY_WALLET_HEX_LEN or not t.startswith(_HEX_PREFIX):
        return False
    return all(c in "0123456789abcdefABCDEF" for c in t[2:])


def normalized_proxy_wallet(raw: str) -> str:
    """Return canonical ``0x`` + lower-hex for a valid proxy wallet string."""
    t = raw.strip()
    return _HEX_PREFIX + t[2:].lower()


def resolve_user_to_proxy_wallet(user: str) -> str:
    """
    Resolve ``user`` to a proxy wallet: either a normalized ``0x…`` address or a
    handle resolved via Gamma / leaderboard (same rules as :func:`fetchUserInfo`).
    """
    raw = (user or "").strip()
    if not raw:
        raise PolymwkError("user is required")
    if is_proxy_wallet_address(raw):
        return normalized_proxy_wallet(raw)
    proxy, _ = resolve_handle_to_proxy_wallet(raw)
    return proxy


def open_position_from_data_api(p: DataApiOpenPosition) -> Position:
    """Map Data API ``GET /positions`` row → :class:`~polymwk.models.Position`."""
    return Position(
        wallet=str(p.proxy_wallet),
        market_slug=p.slug,
        market_title=p.title,
        outcome=p.outcome,
        size=p.size,
        avg_price=p.avg_price,
        current_price=p.current_price,
        current_value=p.current_value,
        unrealised_pnl=p.cash_pnl,
        realised_pnl=p.realized_pnl,
    )


def open_positions_from_data_api(rows: list[DataApiOpenPosition]) -> list[Position]:
    return [open_position_from_data_api(p) for p in rows]


def closed_position_from_data_api(p: DataApiClosedPosition) -> UserClosedPosition:
    """Map Data API ``GET /closed-positions`` row → :class:`~polymwk.models.UserClosedPosition`."""
    return UserClosedPosition(
        wallet=str(p.proxy_wallet),
        market_slug=p.slug,
        market_title=p.title,
        outcome=p.outcome,
        avg_price=p.avg_price,
        current_price=p.current_price,
        total_bought=p.total_bought,
        realized_pnl=p.realized_pnl,
        closed_at=p.timestamp,
        condition_id=str(p.condition_id),
    )


def closed_positions_from_data_api(rows: list[DataApiClosedPosition]) -> list[UserClosedPosition]:
    return [closed_position_from_data_api(p) for p in rows]


def activity_from_data_api(a: DataApiActivity) -> Activity:
    """Map Data API ``GET /activity`` row → :class:`~polymwk.models.Activity`."""
    cid = str(a.condition_id)
    parts = [a.outcome]
    if a.side:
        parts.append(a.side)
    parts.append(f"{a.size:g} @ {a.price:.4f}")
    detail = " · ".join(parts)
    return Activity(
        wallet=str(a.proxy_wallet),
        type=str(a.type),
        timestamp=a.timestamp,
        market_slug=a.slug or None,
        detail=detail,
        market_title=a.title,
        outcome=a.outcome,
        side=a.side,
        size=a.size,
        usdc_size=a.usdc_size,
        price=a.price,
        condition_id=cid,
        transaction_hash=str(a.transaction_hash),
        event_slug=a.event_slug,
    )


def activities_from_data_api(rows: list[DataApiActivity]) -> list[Activity]:
    return [activity_from_data_api(a) for a in rows]


def trade_from_data_api(t: DataApiTrade) -> Trade:
    """Map Data API ``GET /trades`` row → :class:`~polymwk.models.Trade`."""
    sz = float(t.size)
    pr = float(t.price)
    return Trade(
        wallet=str(t.proxy_wallet),
        market_slug=t.slug,
        market_title=t.title,
        side=str(t.side),
        outcome=(t.outcome or "").strip() or "—",
        price=pr,
        size=sz,
        value_usd=sz * pr,
        timestamp=t.timestamp,
        tx_hash=str(t.transaction_hash),
    )


def trades_from_data_api(rows: list[DataApiTrade]) -> list[Trade]:
    return [trade_from_data_api(t) for t in rows]


def leaderboard_entry_from_data_api(row: DataApiLeaderboardUser) -> LeaderboardEntry:
    """Map Data API :class:`~polymarket_apis.types.data_types.LeaderboardUser` → :class:`~polymwk.models.LeaderboardEntry`."""
    return LeaderboardEntry(
        rank=int(row.rank),
        proxy_wallet=str(row.proxy_wallet),
        username=(row.username or "").strip(),
        pnl=float(row.pnl),
        volume_usd=float(row.vol),
        profile_image=(row.profile_image or "").strip(),
        verified_badge=bool(row.verified_badge),
    )


def user_leaderboard_rank_from_lb_api(
    rank_row: DataApiUserRank,
    *,
    metric: Literal["profit", "volume"],
    window: Literal["1d", "7d", "30d", "all"],
    other_metric_row: DataApiUserMetric | None,
) -> UserLeaderboardRank:
    """Map ``lb-api`` rank (+ optional cross metric) → :class:`~polymwk.models.UserLeaderboardRank`."""
    other_amt = float(other_metric_row.amount) if other_metric_row is not None else None
    return UserLeaderboardRank(
        proxy_wallet=str(rank_row.proxy_wallet),
        rank=int(rank_row.rank),
        metric=metric,
        window=window,
        ranked_amount=float(rank_row.amount),
        other_metric_amount=other_amt,
        name=(rank_row.name or "").strip(),
        pseudonym=(getattr(rank_row, "pseudonym", None) or "").strip(),
        bio=(rank_row.bio or "").strip(),
        profile_image=(rank_row.profile_image or "").strip(),
    )


def _normalize_handle(raw: str) -> str:
    s = raw.strip()
    if s.startswith("@"):
        s = s[1:].strip()
    return s


def resolve_handle_to_proxy_wallet(handle: str) -> tuple[str, str]:
    """
    Return ``(proxy_wallet, profile_slug)`` for a Polymarket username (e.g. ``reflex102``).

    Uses Gamma profile search, then Data API leaderboard as fallback.
    ``profile_slug`` is lowercased for stable ``https://polymarket.com/@…`` URLs.
    """
    key = _normalize_handle(handle)
    if not key:
        raise PolymwkError("user handle is empty")
    hl = key.lower()

    gamma = get_gamma_client()
    try:
        res = gamma.search(key, search_profiles=True, limit_per_type=25)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma profile search failed") from exc

    for p in res.profiles or []:
        if not p.proxy_wallet:
            continue
        name = (p.name or "").strip()
        if name.lower() == hl:
            return (str(p.proxy_wallet), hl)

    with_wallet = [p for p in (res.profiles or []) if p.proxy_wallet]
    if len(with_wallet) == 1:
        p = with_wallet[0]
        slug = (p.name or key).strip().lower()
        return (str(p.proxy_wallet), slug)

    data = get_data_client()
    try:
        rows = data.get_leaderboard_rankings(
            username=key, limit=50, time_period="ALL", order_by="VOL"
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Data API leaderboard lookup failed") from exc

    for row in rows:
        if row.username.strip().lower() == hl:
            return (str(row.proxy_wallet), hl)

    raise PolymwkError(f"Polymarket user not found for handle {key!r}")


def enrich_user_stats(proxy: str) -> dict[str, float | int | None | list[float]]:
    """Data API: positions value, biggest closed win, markets traded, all-time PnL."""
    out: dict[str, float | int | None | list[float]] = {
        "positions_value_usd": None,
        "biggest_win_usd": None,
        "markets_traded": None,
        "profit_loss_all_usd": None,
        "pnl_history": [],
    }
    addr = EthAddress(proxy)
    dc = get_data_client()
    try:
        out["positions_value_usd"] = float(dc.get_value(addr).value)
    except (httpx.HTTPError, IndexError, KeyError, ValueError):
        pass
    try:
        out["markets_traded"] = int(dc.get_total_markets_traded(addr))
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        pass
    try:
        um = dc.get_user_metric(addr, metric="profit", window="all")
        out["profit_loss_all_usd"] = float(um.amount)
    except (httpx.HTTPError, IndexError, KeyError, ValueError):
        pass
    try:
        pnl_pts = dc.get_pnl(addr, period="all", frequency="1d")
        out["pnl_history"] = [float(p.value) for p in pnl_pts]
    except (httpx.HTTPError, ValueError, TypeError):
        out["pnl_history"] = []
    try:
        closed = dc.get_closed_positions(addr)
        if closed:
            out["biggest_win_usd"] = float(max(p.realized_pnl for p in closed))
    except (httpx.HTTPError, ValueError, TypeError):
        pass
    return out


def user_info_from_profile(
    prof: UserProfile,
    *,
    query: str,
    profile_slug: str,
) -> UserInfo:
    slug = profile_slug.strip().lower()
    url = f"https://polymarket.com/@{slug}" if slug else ""
    identities: list[UserIdentity] = []
    if prof.users:
        for u in prof.users:
            identities.append(
                UserIdentity(
                    id=str(u.id),
                    creator=bool(u.creator),
                    mod=bool(u.mod),
                    community_mod=u.community_mod,
                )
            )
    return UserInfo(
        proxy_wallet=str(prof.proxy_wallet),
        pseudonym=prof.pseudonym or "",
        name=prof.name,
        bio=prof.bio,
        profile_image=prof.profile_image,
        created_at=prof.created_at,
        display_username_public=bool(prof.display_username_public),
        x_username=prof.x_username,
        verified_badge=bool(prof.verified_badge),
        profile_slug=slug,
        profile_url=url,
        query=query.strip(),
        identities=identities,
    )


def minimal_user_info(proxy: str, query: str) -> UserInfo:
    """Placeholder :class:`~polymwk.models.UserInfo` when Gamma has no public profile (404)."""
    return UserInfo(
        proxy_wallet=proxy,
        query=query.strip(),
        profile_slug="",
        profile_url="",
    )
