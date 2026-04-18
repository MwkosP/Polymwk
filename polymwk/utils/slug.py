"""Market slug helpers."""


def normalize_market_slug(slug: str) -> str:
    """Return a canonical slug string for caches and lookups."""
    return slug.strip()
