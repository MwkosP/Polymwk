"""polymwk-specific errors (wrap vendor / resolution failures)."""


class PolymwkError(Exception):
    """Base error for all polymwk failures."""


class PolymwkResolutionError(PolymwkError):
    """Slug could not be mapped to Polymarket internal IDs (Gamma / cache)."""


class PolymwkApiError(PolymwkError):
    """Upstream HTTP or vendor client failure."""
