"""User trade fills from the Data API (``GET /trades``)."""

from __future__ import annotations

import httpx
from typing import Literal

from polymarket_apis.types.common import EthAddress

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Trade
from polymwk._internal.data import get_data_client
from polymwk.users import utils as user_utils

_MAX_TRADES_PAGE = 500


def fetchUserTrades(
    user: str,
    *,
    limit: int = 100,
    offset: int = 0,
    taker_only: bool = True,
    side: Literal["BUY", "SELL"] | None = None,
    buy_only: bool = False,
    sell_only: bool = False,
    outcome_filter: Literal["any", "yes", "no"] = "any",
    yes_only: bool = False,
    no_only: bool = False,
    condition_id: str | list[str] | None = None,
    event_id: str | int | list[str] | list[int] | None = None,
    filter_type: Literal["CASH", "TOKENS"] | None = None,
    filter_amount: float | None = None,
) -> list[Trade]:
    """
    Load a **page of trade fills** for a user from ``GET /trades``.

    ``user`` is a proxy wallet ``0x…`` or a username / ``@handle`` (resolved like
    :func:`fetchUserInfo`).

    One HTTP request per call; ``limit`` is clamped to **500**. Use ``offset`` to
    page. Optional filters match the Data API (``condition_id`` / ``event_id`` /
    ``taker_only`` / ``filter_type`` + ``filter_amount``).

    **Buy / sell** — ``side='BUY'`` or ``'SELL'``, or ``buy_only=True`` /
    ``sell_only=True``. **Yes / No** — ``outcome_filter='yes'|'no'`` or ``yes_only`` /
    ``no_only`` (client-side, same rules as :func:`fetchUserActivity`).

    Complements :func:`fetchUserActivity` (broader activity stream vs trade ledger only).
    """
    if limit <= 0:
        return []
    if filter_type is not None and filter_amount is None:
        raise PolymwkError("filter_amount is required when filter_type is set")
    if filter_amount is not None and filter_type is None:
        raise PolymwkError("filter_type is required when filter_amount is set")

    eff_side = user_utils.resolve_buy_sell_side(
        side,
        buy_only=buy_only,
        sell_only=sell_only,
        caller="fetchUserTrades",
    )
    eff_outcome = user_utils.resolve_yes_no_outcome(
        outcome_filter,
        yes_only=yes_only,
        no_only=no_only,
        caller="fetchUserTrades",
    )

    proxy = user_utils.resolve_user_to_proxy_wallet(user)
    lim = min(limit, _MAX_TRADES_PAGE)
    off = max(0, offset)

    dc = get_data_client()
    try:
        raw = dc.get_trades(
            limit=lim,
            offset=off,
            taker_only=taker_only,
            user=EthAddress(proxy),
            side=eff_side,
            condition_id=condition_id,
            event_id=event_id,
            filter_type=filter_type,
            filter_amount=filter_amount,
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Data API /trades request failed") from exc

    rows = user_utils.trades_from_data_api(raw)
    if eff_outcome != "any":
        rows = [
            t
            for t in rows
            if user_utils.row_matches_outcome_filter(t.outcome, eff_outcome)
        ]
    return rows
