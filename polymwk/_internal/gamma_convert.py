"""Gamma API types → polymwk public models."""

from __future__ import annotations

import json
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import httpx
from polymarket_apis import PolymarketReadOnlyClobClient
from polymarket_apis.types.gamma_types import Event as GammaEvent
from polymarket_apis.types.gamma_types import GammaMarket
from polymarket_apis.utilities.endpoints import MID_POINTS

from polymwk._internal.clob import get_clob_client
from polymwk.models import Event, Market

_CLOB_MID_BATCH = 75
_CLOB_MID_FETCH_WORKERS = 12


def _float_val(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _clamp_unit(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _as_datetime(value: object | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return None


def _gamma_market_24h_volume(m: GammaMarket) -> float | None:
    """
    Return 24h volume when Gamma reports it; ``None`` when no 24h fields exist
    (distinct from a reported ``0``).
    """
    if m.volume_24hr is not None:
        return _float_val(m.volume_24hr)
    clob_set = m.volume_24hr_clob is not None
    amm_set = m.volume_24hr_amm is not None
    if clob_set or amm_set:
        return _float_val(m.volume_24hr_clob) + _float_val(m.volume_24hr_amm)
    return None


def _gamma_event_24h_volume(event: GammaEvent) -> float | None:
    if event.volume_24hr is not None:
        return _float_val(event.volume_24hr)
    markets = event.markets or []
    return _gamma_event_24h_volume_from_markets(markets)


def _gamma_event_24h_volume_from_markets(markets: list[GammaMarket]) -> float | None:
    if not markets:
        return None
    parts = [_gamma_market_24h_volume(m) for m in markets]
    if all(p is None for p in parts):
        return None
    return sum((p if p is not None else 0.0) for p in parts)


def _gamma_market_is_open_listing(m: GammaMarket) -> bool:
    """Tradeable row like the site: not closed, not inactive, not archived."""
    if m.closed is True:
        return False
    if m.active is False:
        return False
    if m.archived is True:
        return False
    return True


def _json_list(value: object) -> list[object] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, list) else None
    return None


def _clob_outcome_token_ids(m: GammaMarket) -> tuple[str, str]:
    """``(yes_token_id, no_token_id)`` from Gamma ``clobTokenIds`` (binary markets)."""
    ids = _json_list(m.token_ids)
    if not ids:
        return ("", "")
    yes = str(ids[0])
    no = str(ids[1]) if len(ids) > 1 else ""
    return (yes, no)


def _clob_yes_token_id(m: GammaMarket) -> str | None:
    """First CLOB token is the YES outcome (Polymarket convention)."""
    y, _ = _clob_outcome_token_ids(m)
    return y if y else None


def _gamma_markets_for_event(
    event: GammaEvent, *, only_open_markets: bool
) -> list[GammaMarket]:
    raw_markets = list(event.markets or [])
    if only_open_markets:
        return [m for m in raw_markets if _gamma_market_is_open_listing(m)]
    return raw_markets


def prefetch_clob_mids_for_gamma_events(
    events: Sequence[GammaEvent], *, only_open_markets: bool
) -> dict[str, float]:
    """
    One CLOB pass for many events (used by :func:`~polymwk.events.fetch.fetchEvents`).

    Without this, each event would repeat batch + fallback calls.
    """
    ordered: list[str] = []
    for event in events:
        for m in _gamma_markets_for_event(event, only_open_markets=only_open_markets):
            tid = _clob_yes_token_id(m)
            if tid:
                ordered.append(tid)
    unique = list(dict.fromkeys(ordered))
    return _fetch_clob_mid_cache(unique)


def _post_midpoints_raw(clob: PolymarketReadOnlyClobClient, token_ids: list[str]) -> dict[str, float]:
    """Parse ``POST /midpoints`` JSON without pydantic (empty ``{}`` is valid)."""
    if not token_ids:
        return {}
    data = [{"token_id": tid} for tid in token_ids]
    r = clob.client.post(clob._build_url(MID_POINTS), json=data)
    r.raise_for_status()
    body = r.json()
    if not isinstance(body, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in body.items():
        try:
            out[str(k)] = _clamp_unit(float(v))
        except (TypeError, ValueError):
            continue
    return out


def _merge_midpoints_parallel(
    clob: PolymarketReadOnlyClobClient, token_ids: list[str], cache: dict[str, float]
) -> None:
    missing = [tid for tid in token_ids if tid not in cache]
    if not missing:
        return

    def _one_mid(tid: str) -> tuple[str, float | None]:
        try:
            return tid, _clamp_unit(clob.get_midpoint(tid).value)
        except httpx.HTTPError:
            return tid, None

    with ThreadPoolExecutor(max_workers=_CLOB_MID_FETCH_WORKERS) as pool:
        futures = [pool.submit(_one_mid, tid) for tid in missing]
        for fut in as_completed(futures):
            tid, val = fut.result()
            if val is not None:
                cache[tid] = val


def _fetch_clob_mid_cache(token_ids: list[str]) -> dict[str, float]:
    """Batch + per-token fallback; values match UI ``GET /midpoint``."""
    if not token_ids:
        return {}
    clob = get_clob_client()
    cache: dict[str, float] = {}
    for i in range(0, len(token_ids), _CLOB_MID_BATCH):
        chunk = token_ids[i : i + _CLOB_MID_BATCH]
        try:
            part = _post_midpoints_raw(clob, chunk)
            for tid, val in part.items():
                cache[str(tid)] = val
        except httpx.HTTPError:
            _merge_midpoints_parallel(clob, chunk, cache)
    _merge_midpoints_parallel(clob, token_ids, cache)
    return cache


def _yes_mid_from_clob_cache(token_id: str, cache: dict[str, float]) -> float | None:
    return cache.get(token_id)


def _yes_no_from_outcome_row(prices: list[object], outcomes: object) -> tuple[float, float]:
    """Map two outcome prices to (yes, no) using Gamma ``outcomes`` order when present."""
    if len(prices) < 2:
        p0 = _float_val(prices[0], 0.0) if prices else 0.0
        return (p0, max(0.0, min(1.0, 1.0 - p0)))
    p0, p1 = _float_val(prices[0], 0.0), _float_val(prices[1], 0.0)
    outs = _json_list(outcomes)
    if outs is not None and len(outs) >= 2:
        o0 = str(outs[0]).strip().casefold()
        o1 = str(outs[1]).strip().casefold()
        if o0 == "yes" and o1 == "no":
            return (p0, p1)
        if o0 == "no" and o1 == "yes":
            return (p1, p0)
    return (p0, p1)


def _is_pure_yes_no_corner(yes_p: float, no_p: float, *, eps: float = 1e-5) -> bool:
    """True when Gamma shows a fully resolved binary (0% / 100% or the swap)."""
    return (
        (yes_p <= eps and no_p >= 1.0 - eps)
        or (yes_p >= 1.0 - eps and no_p <= eps)
    )


def _coerce_outcome_price_list(m: GammaMarket) -> list[object] | None:
    raw = m.outcome_prices
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else None
        except json.JSONDecodeError:
            return None
    return None


def _yes_no_from_order_book(
    m: GammaMarket, *, max_spread: float = 0.45
) -> tuple[float, float] | None:
    bid, ask = m.best_bid, m.best_ask
    if bid is not None and ask is not None:
        b, a = _float_val(bid), _float_val(ask)
        if 0.0 <= b <= 1.0 and 0.0 <= a <= 1.0 and a >= b:
            spread = a - b
            if spread <= max_spread:
                yes = max(0.0, min(1.0, (b + a) / 2.0))
                return (yes, max(0.0, min(1.0, 1.0 - yes)))
    if bid is not None and ask is None:
        y = max(0.0, min(1.0, _float_val(bid)))
        return (y, max(0.0, min(1.0, 1.0 - y)))
    if ask is not None and bid is None:
        y = max(0.0, min(1.0, _float_val(ask)))
        return (y, max(0.0, min(1.0, 1.0 - y)))
    return None


def _yes_no_prices_gamma_fallback(m: GammaMarket) -> tuple[float, float]:
    """
    Gamma-only fallback when CLOB has no book for the YES token.

    Prefer non-corner ``outcomePrices``, then Gamma best bid/ask / last trade.
    """
    prices_list = _coerce_outcome_price_list(m)
    if prices_list and len(prices_list) >= 1:
        yes_o, no_o = _yes_no_from_outcome_row(prices_list, m.outcomes)
        if not _is_pure_yes_no_corner(yes_o, no_o):
            return (yes_o, no_o)

        ob = _yes_no_from_order_book(m, max_spread=0.35)
        if ob is not None:
            return ob

        last = m.last_trade_price
        if last is not None:
            y = _float_val(last)
            if 0.0 <= y <= 1.0:
                return (y, max(0.0, min(1.0, 1.0 - y)))

        return (yes_o, no_o)

    ob = _yes_no_from_order_book(m, max_spread=0.55)
    if ob is not None:
        return ob

    last = m.last_trade_price
    if last is not None:
        y = _float_val(last)
        if 0.0 <= y <= 1.0:
            return (y, max(0.0, min(1.0, 1.0 - y)))

    return (0.0, 0.0)


def gamma_market_to_polymwk(
    m: GammaMarket, *, yes_from_clob: float | None = None
) -> Market:
    if yes_from_clob is not None:
        y = _clamp_unit(yes_from_clob)
        n = _clamp_unit(1.0 - y)
    else:
        y, n = _yes_no_prices_gamma_fallback(m)
    yt, nt = _clob_outcome_token_ids(m)
    cid = m.condition_id
    return Market(
        slug=m.slug or "",
        question=m.question or "",
        yes_price=y,
        no_price=n,
        yes_token_id=yt,
        no_token_id=nt,
        internal_id=str(m.id).strip() if m.id is not None else "",
        condition_id=str(cid).strip() if cid is not None else "",
        volume=_float_val(m.volume_num) or _float_val(m.volume),
        volume_24h=_gamma_market_24h_volume(m),
        liquidity=_float_val(m.liquidity_num) or _float_val(m.liquidity),
        end_date=_as_datetime(m.end_date) or _as_datetime(m.end_date_iso),
        active=bool(m.active) if m.active is not None else True,
    )


def gamma_event_to_polymwk(
    event: GammaEvent,
    *,
    only_open_markets: bool = False,
    clob_mid_cache: dict[str, float] | None = None,
) -> Event:
    gmarkets = _gamma_markets_for_event(event, only_open_markets=only_open_markets)
    vol_24h = (
        _gamma_event_24h_volume_from_markets(gmarkets)
        if only_open_markets
        else _gamma_event_24h_volume(event)
    )
    yes_tokens = [_clob_yes_token_id(m) for m in gmarkets]
    unique = list(dict.fromkeys(t for t in yes_tokens if t))
    mid_cache = (
        clob_mid_cache
        if clob_mid_cache is not None
        else _fetch_clob_mid_cache(unique)
    )

    markets = [
        gamma_market_to_polymwk(
            m,
            yes_from_clob=_yes_mid_from_clob_cache(tok, mid_cache) if tok else None,
        )
        for m, tok in zip(gmarkets, yes_tokens, strict=True)
    ]
    first = markets[0] if markets else None
    return Event(
        id=str(event.id),
        slug=event.slug or "",
        title=event.title or "",
        description=event.description or "",
        markets=markets,
        market_count=len(markets),
        volume=_float_val(event.volume),
        volume_24h=vol_24h,
        active=bool(event.active) if event.active is not None else True,
        end_date=_as_datetime(event.end_date),
        primary_yes_price=first.yes_price if first else None,
        primary_no_price=first.no_price if first else None,
    )
