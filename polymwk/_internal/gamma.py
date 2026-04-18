"""Shared PolymarketGammaClient instance."""

from polymarket_apis import PolymarketGammaClient

_gamma: PolymarketGammaClient | None = None


def get_gamma_client() -> PolymarketGammaClient:
    global _gamma
    if _gamma is None:
        _gamma = PolymarketGammaClient()
    return _gamma
