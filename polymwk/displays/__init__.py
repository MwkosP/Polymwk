"""Console-friendly views of polymwk data."""

from polymwk.displays.events import (
    displayEvent,
    displayEventComments,
    displayEvents,
    displayMarket,
    displayMarketLastActivity,
    displayMarketPrices,
    displayMarketResolution,
    displayMarketRules,
    displayMarketTopHolders,
    displayMarketUsersPositions,
    displayOrderBook,
    displaySerie,
    displaySeries,
    displayTags,
)
from polymwk.displays.feed import displayLiveOrderBook
from polymwk.displays.users import (
    displayUserActivity,
    displayUserInfo,
    displayUserLeaderboardRank,
    displayUsersLeaderboard,
    displayUserPositions,
    displayUserTrades,
)

__all__ = [
    "displayEvent",
    "displayEventComments",
    "displayEvents",
    "displayMarket",
    "displayMarketLastActivity",
    "displayMarketPrices",
    "displayMarketResolution",
    "displayMarketRules",
    "displayMarketTopHolders",
    "displayMarketUsersPositions",
    "displayLiveOrderBook",
    "displayOrderBook",
    "displaySerie",
    "displaySeries",
    "displayTags",
    "displayUserActivity",
    "displayUserInfo",
    "displayUserLeaderboardRank",
    "displayUsersLeaderboard",
    "displayUserPositions",
    "displayUserTrades",
]
