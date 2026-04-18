from polymwk import displayUserInfo, fetchUserInfo, fetchUserPositions, displayUserPositions,fetchUserActivity, displayUserActivity,fetchUserTrades, displayUserTrades,fetchUserLeaderboardRank, displayUserLeaderboardRank,fetchUsersLeaderboard, displayUsersLeaderboard

# Session Polymarket user — https://polymarket.com/@reflex102
user = "0x61270a2fbd3b5d4ef8d2c23cb8b6fb4df3bfd154"   #0xb39ed64a8c85e93f726b669a750ae34bb18ccd5f   0x61270a2fbd3b5d4ef8d2c23cb8b6fb4df3bfd154  0x1820cd0869ab9479dc14455db55dd35c60b42aa0   0x44356793d11ace7e5f8f36b0d12ed0758c840c4b   0xefbc5fec8d7b0acdc8911bdd9a98d6964308f9a2


# User Info
session_user = fetchUserInfo(user)
displayUserInfo(session_user)

# User Positions
open_ = fetchUserPositions(user, limit=50, status="active")
closed = fetchUserPositions(user, limit=200, status="closed")
displayUserPositions(open_, status="active")
displayUserPositions(closed, status="closed")


# User Activity
act = fetchUserActivity(user, limit=100, offset=0)
displayUserActivity(act)

# User Trades
trades_taker = fetchUserTrades(user, limit=50, offset=0, taker_only=False)
trades_maker = fetchUserTrades(user, limit=50, offset=0, taker_only=True)
displayUserTrades(trades_taker)
displayUserTrades(trades_maker)

# Leaderboard Rank
lb = fetchUserLeaderboardRank(user, metric="profit", window="all", include_cross_metric=True)
displayUserLeaderboardRank(lb)


board = fetchUsersLeaderboard(timeframe="weekly", category="all", order_by="pnl", limit=25)
displayUsersLeaderboard(board)