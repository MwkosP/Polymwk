"""CLOB price history for one outcome token (``/prices-history``)."""

from __future__ import annotations

from typing import Literal

import httpx

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Event, Market, MarketPricePoint, MarketPricesSnapshot
from polymwk._internal.clob import get_clob_client
from polymwk._internal.gamma import get_gamma_client
from polymarket_apis.types.clob_types import PriceHistory

PriceInterval = Literal["1h", "6h", "1d", "1w", "1m", "max"]

_DEFAULT_FIDELITY: dict[PriceInterval, int] = {
    "1h": 1,
    "6h": 1,
    "1d": 1,
    "1w": 5,
    "1m": 10,
    "max": 2,
}


def _yes_no_token_ids(market: str | Market) -> tuple[str, str, str]:
    if isinstance(market, Market):
        y, n = (market.yes_token_id or "").strip(), (market.no_token_id or "").strip()
        if not y or not n:
            raise PolymwkError(
                "Market missing yes_token_id / no_token_id — use markets from fetchEvents"
            )
        return y, n, market.slug.strip()
    slug = str(market).strip()
    if not slug:
        raise PolymwkError("market slug required for fetchMarketPrices")
    try:
        gm = get_gamma_client().get_market_by_slug(slug)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma market-by-slug request failed") from exc
    ids = gm.token_ids or []
    if len(ids) < 2:
        raise PolymwkError(f"Gamma market {slug!r} missing clobTokenIds")
    return str(ids[0]), str(ids[1]), (gm.slug or slug).strip()


def _snapshot_from_price_history(
    ph: PriceHistory,
    *,
    market_slug: str,
    outcome_label: str,
    interval: str,
    fidelity: int,
    event_slug: str,
) -> MarketPricesSnapshot:
    pts = [
        MarketPricePoint(timestamp=h.timestamp, price=float(h.value))
        for h in (ph.history or [])
    ]
    return MarketPricesSnapshot(
        market_slug=market_slug,
        token_id=str(ph.token_id),
        outcome_label=outcome_label,
        interval=interval,
        fidelity=fidelity,
        event_slug=event_slug.strip(),
        points=pts,
    )


def fetchMarketPrices(
    market: str | Market,
    *,
    outcome: Literal["yes", "no"] = "yes",
    interval: PriceInterval = "1d",
    fidelity: int | None = None,
    event_slug: str = "",
) -> MarketPricesSnapshot:
    """
    Load **implied probability** time series for one **market** outcome (CLOB token).

    Uses ``GET /prices-history`` on the **Yes** or **No** token (default Yes, matching
    the site’s primary chart). Pass a :class:`~polymwk.models.Market` from
    ``fetchEvents`` or a **market slug** (Gamma resolves ``clobTokenIds``).

    ``interval``: ``1h`` | ``6h`` | ``1d`` | ``1w`` | ``1m`` | ``max``. ``fidelity`` is
    bucket size in **minutes**; if omitted, the minimum allowed for that interval is used.
    """
    yes_tok, no_tok, mslug = _yes_no_token_ids(market)
    token = yes_tok if outcome == "yes" else no_tok
    label = "Yes" if outcome == "yes" else "No"
    fid = fidelity if fidelity is not None else _DEFAULT_FIDELITY[interval]

    clob = get_clob_client()
    try:
        ph = clob.get_recent_history(token, interval=interval, fidelity=fid)
    except httpx.HTTPError as exc:
        raise PolymwkApiError("CLOB /prices-history request failed") from exc
    except ValueError as exc:
        raise PolymwkError(str(exc)) from exc

    return _snapshot_from_price_history(
        ph,
        market_slug=mslug,
        outcome_label=label,
        interval=interval,
        fidelity=fid,
        event_slug=event_slug,
    )


def fetchEventPrices(
    event: Event,
    *,
    market_index: int = 0,
    outcome: Literal["yes", "no"] = "yes",
    interval: PriceInterval = "1d",
    fidelity: int | None = None,
) -> MarketPricesSnapshot:
    """
    Same as :func:`fetchMarketPrices` for **one market** inside an **event** (default
    first market). Use :func:`fetchMarketPrices` when you already have a
    :class:`~polymwk.models.Market`.
    """
    if not event.markets:
        raise PolymwkError("event has no markets for fetchEventPrices")
    if market_index < 0 or market_index >= len(event.markets):
        raise PolymwkError("market_index out of range for fetchEventPrices")
    return fetchMarketPrices(
        event.markets[market_index],
        outcome=outcome,
        interval=interval,
        fidelity=fidelity,
        event_slug=event.slug,
    )
