"""Shared Polymarket Data API client (holders, activity, …)."""

from __future__ import annotations

from typing import Any, Literal

from polymarket_apis import PolymarketDataClient

_data: PolymarketDataClient | None = None


def get_data_client() -> PolymarketDataClient:
    global _data
    if _data is None:
        _data = PolymarketDataClient()
    return _data


def get_v1_market_positions(
    condition_id: str,
    *,
    limit: int = 500,
    offset: int = 0,
    status: Literal["OPEN", "CLOSED", "ALL"] = "OPEN",
    sort_by: Literal[
        "TOKENS",
        "CASH_PNL",
        "REALIZED_PNL",
        "TOTAL_PNL",
    ] = "TOTAL_PNL",
    sort_direction: Literal["ASC", "DESC"] = "DESC",
    user: str | None = None,
) -> list[dict[str, Any]]:
    """
    ``GET /v1/market-positions`` — ranked positions per outcome token for one condition.

    Returns a JSON list of ``{ "token": ..., "positions": [ ... ] }`` blocks.
    """
    c = get_data_client()
    params: dict[str, str | int] = {
        "market": condition_id,
        "limit": min(max(limit, 0), 500),
        "offset": max(offset, 0),
        "status": status,
        "sortBy": sort_by,
        "sortDirection": sort_direction,
    }
    if user and str(user).strip():
        params["user"] = str(user).strip()
    r = c.client.get(c._build_url("/v1/market-positions"), params=params)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    return data
