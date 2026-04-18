# polymwk — public API usage

**LLM / agent routing:** start at repo-root [SKILLS.md](../../SKILLS.md), then come back here for API detail.

See also: [ARCHITECTURE.md](ARCHITECTURE.md) (layout, data sources), [RULES.md](RULES.md) (naming, `main.py`, contributor checklist).

Import everything from the package root:

```python
from polymwk import fetchEvents, displayEvents
```

**Returns:** `fetch*` functions return **Pydantic models** or `list[...]` of models. **`display*`** functions print to the terminal (default **stdout**) and return **`None`**.

---

## Constants

| Name | Role |
|------|------|
| `DEFAULT_EVENT_LIMIT` | Default cap when `fetchEvents(..., limit=None)`. |
| `DEFAULT_SEARCH_LIMIT` | Default cap for search-style helpers that use it. |

---

## Events & markets (Gamma / CLOB)

| Function | Main arguments | Returns |
|----------|----------------|---------|
| **`fetchEvents`** | `query` (tag slug or list), `limit`, `status` (`"active"` / `"resolved"` / `"all"`), `show_vol`, `get_markets` | `list[Event]` |
| **`fetchEvent`** | Positional **`slug`** *or* `id=` (Gamma event id). Optional: `get_markets`, `show_vol`, `only_open_markets` | `Event` |
| **`fetchMarkets`** | `event` — `Event` instance **or** event **slug** string | `list[Market]` |
| **`fetchMarket`** | Exactly one of: positional **`slug`**, or `id=`, `condition_id=`, `token_id=`. Optional: `show_vol` | `Market` |
| **`fetchSeries`** | `query` (tags), `limit`, `status`, `show_vol`, `event_scan_limit` | `list[Series]` |
| **`fetchSerie`** | Positional **`slug`** *or* `id=`. Optional: `show_vol` | `Series` |
| **`fetchOrderBook`** | `token_id`, optional `market_slug` | `OrderBook` |
| **`fetchEventComments`** | `event` (slug, id, or `Event`), `limit`, `offset`, `order`, `ascending`, … | `EventCommentsSnapshot` |
| **`fetchEventPrices`** | Event + time range params (see docstring in module) | `MarketPricesSnapshot` |
| **`fetchMarketPrices`** | Market slug / id + time params | `MarketPricesSnapshot` |
| **`fetchEventRules`** | Event identifier + options | `MarketRulesSnapshot` |
| **`fetchMarketRules`** | Market slug / `Market` + options | `MarketRulesSnapshot` |
| **`fetchEventResolution`** | Event identifier + options | `MarketResolutionSnapshot` |
| **`fetchMarketResolution`** | Market slug / `Market` + options | `MarketResolutionSnapshot` |
| **`fetchMarketLastActivity`** | Market slug / `Market`, `limit`, … | `MarketLastActivitySnapshot` |
| **`fetchMarketTopHolders`** | `market` (slug or `Market`), `limit`, `min_balance`, `event_slug` | `MarketTopHoldersSnapshot` |
| **`fetchMarketUsersPositions`** | Market slug / `Market`, user filter params | `MarketUsersPositionsSnapshot` |

**Short examples**

```python
evs = fetchEvents("bitcoin", limit=5, status="active")
one = fetchEvent("when-will-bitcoin-hit-150k")
ms = fetchMarkets(one.slug)
m = fetchMarket(slug="will-bitcoin-hit-150k-by-june-30-2026")
series_list = fetchSeries("bitcoin", limit=5)
s = fetchSerie("bitcoin-hit-price-monthly")
book = fetchOrderBook(m.yes_token_id, market_slug=m.slug)
```

---

## Users (Data API)

| Function | Main arguments | Returns |
|----------|----------------|---------|
| **`fetchUserInfo`** | `user` (`0x…` or `@handle`), `include_stats` | `UserInfo` |
| **`fetchUserPositions`** | `user`, `limit`, `status` (`"active"` / `"closed"`) | `list[Position]` or `list[UserClosedPosition]` |
| **`fetchUserActivity`** | `user`, `limit`, `offset`, buy/sell filters, `condition_id`, `event_id`, … | `list[Activity]` |
| **`fetchUserTrades`** | `user`, `limit`, `offset`, `taker_only`, filters… | `list[Trade]` |
| **`fetchUserLeaderboardRank`** | `user`, `metric`, `window`, `include_cross_metric` | `UserLeaderboardRank` |
| **`fetchUsersLeaderboard`** | `timeframe`, `category`, `order_by`, `limit`, `offset` | `UsersLeaderboardSnapshot` |

**Short example**

```python
u = fetchUserInfo("0x61270a2fbd3b5d4ef8d2c23cb8b6fb4df3bfd154")
pos = fetchUserPositions(u.wallet, limit=50, status="active")
```

---

## Config & feed

| Function | Arguments | Returns |
|----------|-----------|---------|
| **`fetchTags`** | (none) | `TagsConfigSnapshot` |
| **`tags`** | Module — keyword tree for `fetchEvents` queries | (import `tags` from `polymwk`) |
| **`subscribeMarketOrderBook`** | `token_id`, `market_slug`, `on_order_book`, `on_best_bid_ask`, … | `None` (blocks until WS ends) |

**Short examples**

```python
cfg = fetchTags()
from polymwk import tags  # configs.tags keyword tree

subscribeMarketOrderBook(
    token_id,
    on_order_book=lambda ob: print(ob.midpoint),
)
```

---

## Displays (terminal)

Each **`display*`** takes model(s) from the matching **`fetch*`** (plus small options: `tags`, `stream`, `status`, …). **Return value:** always **`None`**.

| Display | Typical input |
|---------|----------------|
| `displayEvents` | `list[Event]` |
| `displayEvent` | one `Event` |
| `displayMarket` | one `Market` (`event_title=` optional) |
| `displaySeries` / `displaySerie` | `list[Series]` / one `Series` |
| `displayOrderBook` | `OrderBook` |
| `displayLiveOrderBook` | `token_id` + kwargs (live ladder) |
| `displayTags` | `TagsConfigSnapshot` |
| `displayEventComments` | `EventCommentsSnapshot` |
| `displayMarketPrices`, `displayMarketRules`, `displayMarketResolution`, `displayMarketLastActivity`, `displayMarketTopHolders`, `displayMarketUsersPositions` | matching snapshot types |
| `displayUserInfo`, `displayUserPositions`, `displayUserActivity`, `displayUserTrades` | user models / lists |
| `displayUserLeaderboardRank`, `displayUsersLeaderboard` | rank / leaderboard snapshots |

**Short example**

```python
displayEvents(fetchEvents("nvda", limit=3), tags="nvda", show_markets=True)
displayMarket(fetchMarket("some-market-slug"), event_title="Optional context")
```

---

## Client & errors

| Symbol | Role |
|--------|------|
| **`Polymarket`** | Optional façade; `.resolver` for slug→id (mostly internal). |
| **`PolymwkError`** | Validation / bad arguments. |
| **`PolymwkApiError`** | Upstream HTTP / API failure. |
| **`PolymwkResolutionError`** | Slug resolution not wired. |

---

## Model types (return shapes)

Fetches return instances of types re-exported from **`polymwk`** (e.g. **`Event`**, **`Market`**, **`Series`**, **`OrderBook`**, **`UserInfo`**, **`Trade`**, **`Activity`**, **`Position`**, snapshots like **`MarketTopHoldersSnapshot`**). Use attributes on those objects or pass them straight into **`display*`** functions.

For field-level detail, see docstrings on each function in the **`polymwk/`** source tree.
