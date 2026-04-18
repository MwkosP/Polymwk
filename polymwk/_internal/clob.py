"""Shared read-only CLOB client (midpoints match Polymarket UI)."""

from polymarket_apis import PolymarketReadOnlyClobClient

_clob: PolymarketReadOnlyClobClient | None = None


def get_clob_client() -> PolymarketReadOnlyClobClient:
    global _clob
    if _clob is None:
        _clob = PolymarketReadOnlyClobClient()
    return _clob
