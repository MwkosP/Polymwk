"""Internal helpers for the events package (keep ``fetch.py`` user-facing only)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal

import httpx
from polymarket_apis import PolymarketGammaClient
from polymarket_apis.types.clob_types import OrderBookSummary, OrderSummary
from polymarket_apis.types.data_types import Holder as DataApiHolder
from polymarket_apis.types.data_types import HolderResponse
from polymarket_apis.types.data_types import Trade as DataApiTrade
from polymarket_apis.types.gamma_types import Event as GammaEvent
from polymarket_apis.types.gamma_types import Series as GammaSeries

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import (
    BookLevel,
    Event,
    EventCommentRow,
    EventCommentsSnapshot,
    MarketLastActivityRow,
    MarketLastActivitySnapshot,
    MarketTopHolder,
    MarketTopHoldersGroup,
    MarketTopHoldersSnapshot,
    MarketUserPosition,
    MarketUsersPositionsGroup,
    MarketUsersPositionsSnapshot,
    OrderBook,
    Series,
)
from polymwk._internal.gamma import get_gamma_client
from polymwk._internal.gamma_convert import _float_val

EventFetchStatus = Literal["active", "resolved", "all"]


def parse_event_lookup(
    slug: str | None,
    id: str | None,
) -> tuple[Literal["slug", "id"], str]:
    """Exactly one of slug (positional default) or id= for :func:`~polymwk.events.fetch.fetchEvent`."""
    s_slug = (slug or "").strip()
    s_id = (id or "").strip()
    if s_slug and s_id:
        raise PolymwkError("pass either a slug (positional) or id=, not both")
    if s_slug:
        return ("slug", s_slug)
    if s_id:
        return ("id", s_id)
    raise PolymwkError("provide an event slug (first argument) or id=")


def parse_market_lookup(
    slug: str | None,
    id: str | None,
    condition_id: str | None,
    token_id: str | None,
) -> tuple[Literal["slug", "id", "condition_id", "token_id"], str]:
    """Exactly one identifier for :func:`~polymwk.events.markets.fetchMarket`."""
    pairs: list[tuple[Literal["slug", "id", "condition_id", "token_id"], str]] = []
    if (slug or "").strip():
        pairs.append(("slug", (slug or "").strip()))
    if (id or "").strip():
        pairs.append(("id", (id or "").strip()))
    if (condition_id or "").strip():
        pairs.append(("condition_id", (condition_id or "").strip()))
    if (token_id or "").strip():
        pairs.append(("token_id", (token_id or "").strip()))
    if len(pairs) == 0:
        raise PolymwkError(
            "provide a market slug (positional), or id=, condition_id=, or token_id="
        )
    if len(pairs) > 1:
        raise PolymwkError(
            "pass exactly one of: slug (positional), id=, condition_id=, token_id="
        )
    return pairs[0]


def parse_serie_lookup(
    slug: str | None,
    id: str | None,
) -> tuple[Literal["slug", "id"], str]:
    """Exactly one of slug or id= for :func:`~polymwk.events.series.fetchSerie`."""
    s_slug = (slug or "").strip()
    s_id = (id or "").strip()
    if s_slug and s_id:
        raise PolymwkError("pass either a slug (positional) or id=, not both")
    if s_slug:
        return ("slug", s_slug)
    if s_id:
        return ("id", s_id)
    raise PolymwkError("provide a series slug (first argument) or id=")


def apply_event_fetch_flags(
    ev: Event, *, show_vol: bool, get_markets: bool
) -> Event:
    """Drop volumes and/or market rows according to fetch flags (count is kept)."""
    market_count = len(ev.markets)
    markets = list(ev.markets)
    if not get_markets:
        markets = []
    elif not show_vol:
        markets = [
            m.model_copy(update={"volume": 0.0, "volume_24h": 0.0}) for m in markets
        ]
    return ev.model_copy(
        update={
            "markets": markets,
            "market_count": market_count,
            "volume": ev.volume if show_vol else 0.0,
            "volume_24h": ev.volume_24h if show_vol else 0.0,
        }
    )


def event_status_to_gamma_params(status: EventFetchStatus | None) -> dict[str, Any]:
    if status is None or status == "all":
        return {}
    if status == "active":
        # Event-level: open only. Embedded markets are still filtered in gamma_convert.
        return {"active": True, "closed": False}
    if status == "resolved":
        return {"closed": True}
    raise PolymwkError(
        f"status must be 'active', 'resolved', or 'all', not {status!r}"
    )


def _series_dedupe_key(gs: GammaSeries) -> str:
    if gs.id is not None and str(gs.id).strip():
        return f"id:{gs.id}"
    s = (gs.slug or "").strip()
    return f"slug:{s}" if s else ""


def gamma_series_to_polymwk(gs: GammaSeries, *, event_count: int = 0) -> Series:
    return Series(
        id=str(gs.id).strip() if gs.id is not None else "",
        slug=(gs.slug or "").strip(),
        title=(gs.title or "").strip(),
        subtitle=(gs.subtitle or "").strip(),
        series_type=(gs.series_type or "").strip(),
        recurrence=(gs.recurrence or "").strip(),
        description=(gs.description or "").strip(),
        active=True if gs.active is None else bool(gs.active),
        closed=False if gs.closed is None else bool(gs.closed),
        archived=False if gs.archived is None else bool(gs.archived),
        volume=float(gs.volume or 0.0),
        volume_24h=gs.volume_24hr,
        liquidity=float(gs.liquidity or 0.0),
        event_count=int(event_count),
    )


def apply_series_fetch_flags(s: Series, *, show_vol: bool) -> Series:
    if show_vol:
        return s
    return s.model_copy(
        update={"volume": 0.0, "volume_24h": None, "liquidity": 0.0}
    )


def collect_series_from_tagged_gamma_events(
    client: PolymarketGammaClient,
    raw: list[GammaEvent],
    *,
    status: EventFetchStatus | None,
) -> list[tuple[GammaSeries, int]]:
    """
    Merge embedded ``event.series`` rows and resolve ``series_slug`` via ``get_series`` when needed.
    Returns ``(gamma_series, event_count)`` unsorted.
    """
    agg: dict[str, tuple[GammaSeries, int]] = {}

    closed_param: bool | None
    if status == "active":
        closed_param = False
    elif status == "resolved":
        closed_param = True
    else:
        closed_param = None

    for ev in raw:
        if ev.series:
            for gs in ev.series:
                k = _series_dedupe_key(gs)
                if not k or k == "slug:":
                    continue
                if k in agg:
                    s, c = agg[k]
                    agg[k] = (s, c + 1)
                else:
                    agg[k] = (gs, 1)
            continue
        slug = (ev.series_slug or "").strip()
        if not slug:
            continue
        k = f"slug:{slug}"
        if k in agg:
            s, c = agg[k]
            agg[k] = (s, c + 1)
            continue
        try:
            kwargs: dict[str, Any] = {"limit": 1, "slug": slug}
            if closed_param is not None:
                kwargs["closed"] = closed_param
            part = client.get_series(**kwargs)
        except httpx.HTTPError:
            continue
        if not part:
            continue
        gs = part[0]
        dedupe_k = _series_dedupe_key(gs) or k
        if dedupe_k in agg:
            s, c = agg[dedupe_k]
            agg[dedupe_k] = (s, c + 1)
        else:
            agg[dedupe_k] = (gs, 1)

    return list(agg.values())


def fetch_raw_gamma_events_by_tags(
    client: PolymarketGammaClient,
    tags: Sequence[str],
    cap: int,
    filters: dict[str, Any],
) -> list[GammaEvent]:
    """Gamma ``get_events`` for one or more tag slugs; merge, sort by volume, slice."""
    try:
        if len(tags) == 1:
            return client.get_events(
                limit=min(cap, 500), tag_slug=tags[0], **filters
            )
        pool = min(500, cap * len(tags))
        merged: dict[int, GammaEvent] = {}
        for tag in tags:
            part = client.get_events(limit=pool, tag_slug=tag, **filters)
            for ev in part:
                merged[ev.id] = ev
        raw = list(merged.values())
        raw.sort(key=lambda e: _float_val(e.volume), reverse=True)
        return raw[:cap]
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma /events request failed") from exc


def _best_from_bids(bids: list[OrderSummary]) -> float:
    if not bids:
        return 0.0
    return max(o.price for o in bids)


def _best_from_asks(asks: list[OrderSummary]) -> float:
    if not asks:
        return 1.0
    return min(o.price for o in asks)


def gamma_condition_id_for_market_slug(slug: str) -> str:
    """Resolve Gamma ``conditionId`` for a market slug (Data API ``/holders`` key)."""
    s = slug.strip()
    if not s:
        raise PolymwkError("market slug must be non-empty")
    try:
        gm = get_gamma_client().get_market_by_slug(s)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma market-by-slug request failed") from exc
    cid = gm.condition_id
    if not cid:
        raise PolymwkError(f"no condition_id for market slug {s!r}")
    return str(cid)


def outcome_label_for_index(outcome_index: int) -> str:
    if outcome_index == 0:
        return "Yes"
    if outcome_index == 1:
        return "No"
    return f"Outcome {outcome_index}"


def market_top_holder_from_data(h: DataApiHolder) -> MarketTopHolder:
    return MarketTopHolder(
        wallet=str(h.proxy_wallet),
        size=float(h.amount),
        outcome_index=int(h.outcome_index),
        token_id=str(h.token_id),
        name=(h.name or "").strip(),
        pseudonym=(h.pseudonym or "").strip(),
    )


def market_top_holders_snapshot_from_api(
    market_slug: str,
    condition_id: str,
    responses: list[HolderResponse],
    *,
    event_slug: str = "",
) -> MarketTopHoldersSnapshot:
    groups: list[MarketTopHoldersGroup] = []
    for block in responses:
        rows = [market_top_holder_from_data(h) for h in block.holders]
        label = (
            outcome_label_for_index(block.holders[0].outcome_index)
            if block.holders
            else "—"
        )
        groups.append(
            MarketTopHoldersGroup(
                token_id=str(block.token_id),
                outcome_label=label,
                holders=rows,
            )
        )
    return MarketTopHoldersSnapshot(
        market_slug=market_slug,
        condition_id=condition_id,
        event_slug=event_slug.strip(),
        groups=groups,
    )


def _display_label_market_user_position(wallet: str, name: str) -> str:
    n = name.strip()
    if n:
        return n if len(n) <= 28 else f"{n[:25]}..."
    w = wallet.strip()
    if len(w) <= 22:
        return w
    return f"{w[:10]}...{w[-4:]}"


def market_user_position_from_v1_row(
    p: dict[str, Any],
    *,
    token_id: str,
) -> MarketUserPosition:
    wallet = str(p.get("proxyWallet") or "")
    raw_name = str(p.get("name") or "")
    oi = int(p.get("outcomeIndex") if p.get("outcomeIndex") is not None else 0)
    oc = str(p.get("outcome") or "").strip() or outcome_label_for_index(oi)
    tp = p.get("totalPnl")
    cp = p.get("cashPnl")
    total_pnl = float(tp if tp is not None else cp or 0.0)
    return MarketUserPosition(
        wallet=wallet,
        display_name=_display_label_market_user_position(wallet, raw_name),
        outcome=oc,
        outcome_index=oi,
        avg_price=float(p.get("avgPrice") or 0.0),
        total_pnl=total_pnl,
        cash_pnl=float(cp or 0.0),
        current_value=float(p.get("currentValue") or 0.0),
        token_id=token_id,
    )


def market_users_positions_snapshot_from_v1(
    market_slug: str,
    condition_id: str,
    blocks: list[dict[str, Any]],
    *,
    event_slug: str = "",
) -> MarketUsersPositionsSnapshot:
    groups: list[MarketUsersPositionsGroup] = []
    for block in blocks:
        tid = str(block.get("token") or "")
        raw = block.get("positions")
        if not isinstance(raw, list):
            continue
        rows: list[MarketUserPosition] = []
        for item in raw:
            if isinstance(item, dict):
                rows.append(market_user_position_from_v1_row(item, token_id=tid))
        label = rows[0].outcome if rows else "—"
        groups.append(
            MarketUsersPositionsGroup(
                token_id=tid,
                outcome_label=label,
                positions=rows,
            )
        )
    return MarketUsersPositionsSnapshot(
        market_slug=market_slug,
        condition_id=condition_id,
        event_slug=event_slug.strip(),
        groups=groups,
    )


def trade_activity_display_name(t: DataApiTrade) -> str:
    n = (t.name or "").strip()
    ps = (t.pseudonym or "").strip()
    if n and not n.startswith("0x"):
        return n if len(n) <= 36 else f"{n[:33]}..."
    if ps:
        return ps if len(ps) <= 36 else f"{ps[:33]}..."
    if n:
        return n if len(n) <= 36 else f"{n[:33]}..."
    w = str(t.proxy_wallet)
    if len(w) <= 18:
        return w
    return f"{w[:6]}...{w[-6:]}"


def market_last_activity_row_from_trade(t: DataApiTrade) -> MarketLastActivityRow:
    sz = float(t.size)
    pr = float(t.price)
    tx = getattr(t, "transaction_hash", None)
    tx_s = str(tx) if tx is not None else ""
    return MarketLastActivityRow(
        wallet=str(t.proxy_wallet),
        display_name=trade_activity_display_name(t),
        side=str(t.side).upper(),
        size=sz,
        price=pr,
        outcome=(t.outcome or "").strip() or "—",
        value_usd=sz * pr,
        timestamp=t.timestamp,
        transaction_hash=tx_s,
    )


def market_last_activity_snapshot_from_trades(
    market_slug: str,
    condition_id: str,
    rows: list[DataApiTrade],
    *,
    event_slug: str = "",
) -> MarketLastActivitySnapshot:
    return MarketLastActivitySnapshot(
        market_slug=market_slug,
        condition_id=condition_id,
        event_slug=event_slug.strip(),
        activities=[market_last_activity_row_from_trade(t) for t in rows],
    )


def resolve_gamma_event_for_comments(event: str | int | Event) -> tuple[int, str, str]:
    """Return Gamma numeric ``(event_id, slug, title)`` for comment API lookup."""
    if isinstance(event, Event):
        eid = int(str(event.id).strip())
        return eid, event.slug.strip(), (event.title or "").strip()
    if isinstance(event, int):
        return int(event), "", ""
    s = str(event).strip()
    if not s:
        raise PolymwkError("event slug, numeric id, or Event required for comments")
    if s.isdigit():
        return int(s), "", ""
    try:
        rows = get_gamma_client().get_events(slugs=[s], limit=1)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma events request failed") from exc
    if not rows:
        raise PolymwkError(f"no Gamma event for slug {s!r}")
    ge = rows[0]
    return int(ge.id), (ge.slug or s).strip(), (ge.title or "").strip()


def _parse_gamma_iso_ts(raw: str) -> datetime:
    s = raw.strip()
    if not s:
        return datetime.now(UTC)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def event_comment_display_name_from_profile(
    profile: dict[str, Any] | None,
    user_address: str,
) -> str:
    if profile:
        n = str(profile.get("name") or "").strip()
        ps = str(profile.get("pseudonym") or "").strip()
        pub = profile.get("displayUsernamePublic")
        if pub and n and not n.startswith("0x"):
            return n if len(n) <= 40 else f"{n[:37]}..."
        if ps:
            return ps if len(ps) <= 40 else f"{ps[:37]}..."
        if n:
            return n if len(n) <= 40 else f"{n[:37]}..."
    ua = (user_address or "").strip()
    if len(ua) <= 14:
        return ua
    return f"{ua[:6]}...{ua[-4:]}"


def event_comment_row_from_gamma_dict(c: dict[str, Any]) -> EventCommentRow:
    profile = c.get("profile") if isinstance(c.get("profile"), dict) else None
    ua = str(c.get("userAddress") or "")
    body = str(c.get("body") or "").strip()
    pid = c.get("parentCommentID")
    pcid = str(pid).strip() if pid is not None and str(pid).strip() else None
    raddr = c.get("replyAddress")
    rds = str(raddr).strip() if raddr is not None and str(raddr).strip() else None
    rc = c.get("reactionCount")
    return EventCommentRow(
        id=str(c.get("id") or ""),
        body=body,
        user_address=ua,
        display_name=event_comment_display_name_from_profile(profile, ua),
        created_at=_parse_gamma_iso_ts(str(c.get("createdAt") or "")),
        parent_comment_id=pcid,
        reply_to_address=rds,
        reaction_count=int(rc) if rc is not None else 0,
    )


def event_comments_snapshot_from_gamma_json(
    event_id: int,
    event_slug: str,
    event_title: str,
    rows: list[dict[str, Any]],
) -> EventCommentsSnapshot:
    comments = [event_comment_row_from_gamma_dict(c) for c in rows if isinstance(c, dict)]
    return EventCommentsSnapshot(
        event_id=event_id,
        event_slug=event_slug,
        event_title=event_title,
        comments=comments,
    )


def order_book_from_clob_summary(
    summary: OrderBookSummary,
    *,
    market_slug: str,
) -> OrderBook:
    """Map CLOB ``OrderBookSummary`` to :class:`~polymwk.models.OrderBook`."""
    bids = summary.bids or []
    asks = summary.asks or []
    best_bid = _best_from_bids(bids)
    best_ask = _best_from_asks(asks)
    if bids and asks:
        spread = max(0.0, best_ask - best_bid)
        midpoint = (best_bid + best_ask) / 2.0
    elif bids:
        spread = 0.0
        midpoint = best_bid
    elif asks:
        spread = 0.0
        midpoint = best_ask
    else:
        spread = 1.0
        midpoint = 0.5

    return OrderBook(
        market_slug=market_slug,
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        midpoint=midpoint,
        bids=[BookLevel(price=o.price, size=o.size) for o in bids],
        asks=[BookLevel(price=o.price, size=o.size) for o in asks],
        timestamp=summary.timestamp,
    )
