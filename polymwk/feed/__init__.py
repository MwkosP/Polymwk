"""Live WebSocket / streaming (scaffold).

All public streaming APIs live **only** in this package: **``subscribe<Module><Action>``** (camelCase),
e.g. ``subscribeMarketOrderBook``. REST snapshots stay **``fetch*``** in ``polymwk.events`` / ``users`` / etc.;
do not add **``subscribe*``** outside ``feed/``.
"""

from polymwk.feed.orderbook import subscribeMarketOrderBook

__all__ = ["subscribeMarketOrderBook"]
