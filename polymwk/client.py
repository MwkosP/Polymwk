"""Optional facade that wires internal clients (modules attach here later)."""

from polymwk._internal.resolver import Resolver


class Polymarket:
    """Top-level handle; subsystems will share this resolver and clients."""

    __slots__ = ("_resolver",)

    def __init__(self) -> None:
        self._resolver = Resolver()

    @property
    def resolver(self) -> Resolver:
        """Slug → ID cache (primarily for internal use)."""
        return self._resolver
