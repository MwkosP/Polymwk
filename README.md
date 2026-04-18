# polymwk

Clean, **pip-installable** Python helpers around Polymarket’s public APIs: events and markets, user profiles and positions, leaderboards, tags, order books, and optional live feed wiring.

**Python:** 3.12+

**For LLMs / agents:** [SKILLS.md](SKILLS.md)

**Deeper docs:** [Usage](assets/docs/USAGE.md) · [Architecture](assets/docs/ARCHITECTURE.md) · [Development rules](assets/docs/RULES.md)

---

## Install

From the project root (editable while you develop):

```bash
pip install -e .
```

Or from a built wheel / index once published:

```bash
pip install polymwk
```

Dependencies are declared in `pyproject.toml` (notably `polymarket-apis`, `httpx`, `truststore`, `pydantic`, `polars`, `plotille`).

### TLS on Windows

The package enables [`truststore`](https://pypi.org/project/truststore/) so HTTPS can use the **same OS certificate store** as your browser. If you still see TLS errors (for example hostname mismatch behind aggressive HTTPS scanning), fix or exempt Polymarket in that tool, or point `SSL_CERT_FILE` at a PEM bundle your environment trusts.

---

## Examples

### Events

Search events, then inspect a market: positions, prices, rules, and resolution.

```python
from polymwk import (
    displayEventComments,
    displayEvents,
    displayMarketLastActivity,
    displayMarketPrices,
    displayMarketResolution,
    displayMarketRules,
    displayMarketTopHolders,
    displayMarketUsersPositions,
    displayOrderBook,
    fetchEventComments,
    fetchEventPrices,
    fetchEventResolution,
    fetchEventRules,
    fetchEvents,
    fetchMarketLastActivity,
    fetchMarketTopHolders,
    fetchMarketUsersPositions,
    fetchOrderBook,
)

# Fetch events (Gamma search-style query)
events = fetchEvents(query="bitcoin", limit=5, status="active")
first_market = events[0].markets[0]

# Optional: tabular event list with tag highlighting
# displayEvents(events, tags="nvda", show_markets=True)

# REST order book for one outcome token
# book = fetchOrderBook(first_market.yes_token_id, market_slug=first_market.slug)
# displayOrderBook(book, event_slug=events[0].slug, market_question=first_market.question)

# Market top holders (whales)
# holders = fetchMarketTopHolders(first_market, event_slug=events[0].slug)
# displayMarketTopHolders(holders)

users_positions = fetchMarketUsersPositions(
    first_market, event_slug=events[0].slug, limit=15
)
displayMarketUsersPositions(users_positions)

price_chart = fetchEventPrices(events[0], interval="max")
displayMarketPrices(price_chart)

rules = fetchEventRules(events[0])
displayMarketRules(rules)

resolution = fetchEventResolution(events[0])
displayMarketResolution(resolution)

# Recent fills / activity on a market
# last_activity = fetchMarketLastActivity(
#     first_market, event_slug=events[0].slug, limit=12
# )
# displayMarketLastActivity(last_activity)

# Threaded comments on the event page
# event_comments = fetchEventComments(events[0], limit=8)
# displayEventComments(event_comments)
```

### Users

Use a **proxy wallet** `0x…` or a **handle** (`reflex102` / `@reflex102`). Functions resolve handles via Gamma where needed.

```python
from polymwk import (
    displayUserActivity,
    displayUserInfo,
    displayUserLeaderboardRank,
    displayUserPositions,
    displayUserTrades,
    displayUsersLeaderboard,
    fetchUserActivity,
    fetchUserInfo,
    fetchUserLeaderboardRank,
    fetchUserPositions,
    fetchUserTrades,
    fetchUsersLeaderboard,
)

# Example profile: https://polymarket.com/@reflex102
user = "0x61270a2fbd3b5d4ef8d2c23cb8b6fb4df3bfd154"

session_user = fetchUserInfo(user)
displayUserInfo(session_user)

open_ = fetchUserPositions(user, limit=50, status="active")
closed = fetchUserPositions(user, limit=200, status="closed")
displayUserPositions(open_, status="active")
displayUserPositions(closed, status="closed")

act = fetchUserActivity(user, limit=100, offset=0)
displayUserActivity(act)

trades_taker = fetchUserTrades(user, limit=50, offset=0, taker_only=False)
trades_maker = fetchUserTrades(user, limit=50, offset=0, taker_only=True)
displayUserTrades(trades_taker)
displayUserTrades(trades_maker)

lb = fetchUserLeaderboardRank(
    user, metric="profit", window="all", include_cross_metric=True
)
displayUserLeaderboardRank(lb)

board = fetchUsersLeaderboard(
    timeframe="weekly", category="all", order_by="pnl", limit=25
)
displayUsersLeaderboard(board)
```

### Tags (site-style categories)

```python
from polymwk import displayTags, fetchTags

displayTags(fetchTags())
```

### Tags as query keywords (`configs.tags`)

Use bundled keyword lists (e.g. `BITCOIN`) the same way you might type tags into the site search.

```python
from polymwk import displayEvents, fetchEvents
from polymwk.configs.tags import BITCOIN

events = fetchEvents(query=BITCOIN, limit=50, status="active")
event = events[40]
first_market = event.markets[0]

displayEvents(events, tags="bitcoin", show_markets=True)
```

### Series, single event, market, live order book

Uncomment and adapt when you want slug- or id-based fetches and the live ladder.

```python
from polymwk import (
    displayEvent,
    displayEvents,
    displayLiveOrderBook,
    displayMarket,
    displaySerie,
    displaySeries,
    fetchEvent,
    fetchMarket,
    fetchSerie,
    fetchSeries,
)

# series = fetchSeries(query="bitcoin", limit=50, status="active")
# displaySeries(series, tags="bitcoin")

# ev = fetchEvent("when-will-bitcoin-hit-150k")
# displayEvent(ev)

# m = fetchMarket(slug=ev.markets[0].slug)
# displayMarket(m, event_title=ev.title)

# s = fetchSerie(id="10016")
# displaySerie(s)

# Same ladder as displayOrderBook, redrawn on each WebSocket update (Ctrl+C to stop).
# displayLiveOrderBook(
#     first_market.yes_token_id,
#     market_slug=first_market.slug,
#     event_slug=ev.slug,
#     market_question=first_market.question,
# )
```

### Feed (WebSocket order book)

`subscribeMarketOrderBook` streams CLOB updates for one outcome `token_id` and **blocks** until the socket ends. For a full terminal ladder that redraws on each update, use `displayLiveOrderBook` (see the commented block under **Series, single event, market, live order book**).

```python
from polymwk import subscribeMarketOrderBook

def on_tick(update):
    print(update)

# subscribeMarketOrderBook(
#     token_id,
#     market_slug="optional-slug",
#     on_best_bid_ask=on_tick,
# )
```

---

## Tests

```bash
pip install pytest
pytest
```

(`pyproject.toml` also lists dev tools under `[dependency-groups]` for installers that support dependency groups, for example `uv sync --group dev`.)

