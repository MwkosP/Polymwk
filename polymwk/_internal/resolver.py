"""Translate market slugs to Polymarket internal IDs (cached)."""

from __future__ import annotations

from polymwk.exceptions import PolymwkResolutionError
from polymwk.utils.slug import normalize_market_slug


class Resolver:
    """Translates user-facing slugs to internal Polymarket IDs."""

    def __init__(self) -> None:
        self._yes_by_slug: dict[str, str] = {}
        self._no_by_slug: dict[str, str] = {}
        self._condition_by_slug: dict[str, str] = {}

    def get_token_id(self, slug: str) -> str:
        """Market slug → YES token_id (CLOB order book / price history)."""
        key = normalize_market_slug(slug)
        if key not in self._yes_by_slug:
            self._resolve(key)
        return self._yes_by_slug[key]

    def get_condition_id(self, slug: str) -> str:
        """Market slug → condition_id (Data API / GraphQL)."""
        key = normalize_market_slug(slug)
        if key not in self._condition_by_slug:
            self._resolve(key)
        return self._condition_by_slug[key]

    def get_token_ids(self, slug: str) -> tuple[str, str]:
        """Market slug → (yes_token_id, no_token_id)."""
        key = normalize_market_slug(slug)
        if key not in self._yes_by_slug or key not in self._no_by_slug:
            self._resolve(key)
        return (self._yes_by_slug[key], self._no_by_slug[key])

    def seed(
        self,
        slug: str,
        *,
        yes_token_id: str,
        no_token_id: str,
        condition_id: str,
    ) -> None:
        """Populate cache (tests or future Gamma wiring)."""
        key = normalize_market_slug(slug)
        self._yes_by_slug[key] = yes_token_id
        self._no_by_slug[key] = no_token_id
        self._condition_by_slug[key] = condition_id

    def _resolve(self, normalized_slug: str) -> None:
        raise PolymwkResolutionError(
            f"Cannot resolve slug {normalized_slug!r}: wire PolymarketGammaClient in _internal/gamma.py "
            "or call resolver.seed() for tests."
        )
