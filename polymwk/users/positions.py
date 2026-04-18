"""User positions from the Data API (open / closed)."""

from __future__ import annotations

import httpx
from typing import Literal, overload

from polymarket_apis.types.common import EthAddress

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import Position, UserClosedPosition
from polymwk._internal.data import get_data_client
from polymwk.users import utils as user_utils

UserPositionsStatus = Literal["active", "closed"]


@overload
def fetchUserPositions(
    user: str,
    *,
    limit: int = 100,
    status: Literal["active"] = "active",
) -> list[Position]: ...


@overload
def fetchUserPositions(
    user: str,
    *,
    limit: int = 100,
    status: Literal["closed"],
) -> list[UserClosedPosition]: ...


def fetchUserPositions(
    user: str,
    *,
    limit: int = 100,
    status: UserPositionsStatus = "active",
) -> list[Position] | list[UserClosedPosition]:
    """
    Load positions for a Polymarket user.

    ``user`` is a proxy wallet ``0x…`` or a username / ``@handle`` (resolved like
    :func:`fetchUserInfo`).

    * **``status='active'``** — ``GET /positions`` (open positions). ``limit`` is
      passed through (capped at 500 upstream).
    * **``status='closed'``** — ``GET /closed-positions`` (full history in one
      response). ``limit`` trims **after** the fetch (client-side), newest-first
      if the API returns that order; use a high ``limit`` if you need the full list.
    """
    proxy = user_utils.resolve_user_to_proxy_wallet(user)
    dc = get_data_client()

    if status == "active":
        try:
            raw = dc.get_positions(EthAddress(proxy), limit=limit)
        except httpx.HTTPError as exc:
            raise PolymwkApiError("Data API /positions request failed") from exc
        return user_utils.open_positions_from_data_api(raw)

    try:
        raw = dc.get_closed_positions(EthAddress(proxy))
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Data API /closed-positions request failed") from exc

    rows = user_utils.closed_positions_from_data_api(raw)
    if limit < 1:
        return []
    return rows[:limit]
