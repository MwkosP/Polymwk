"""Shared Polymarket WebSocket client (singleton)."""

from __future__ import annotations

from polymarket_apis import PolymarketWebsocketsClient

_ws: PolymarketWebsocketsClient | None = None


def get_polymarket_websockets_client() -> PolymarketWebsocketsClient:
    global _ws
    if _ws is None:
        _ws = PolymarketWebsocketsClient()
    return _ws
