# polymwk development rules

This file lives in **`assets/docs/`** with [USAGE.md](USAGE.md) and [ARCHITECTURE.md](ARCHITECTURE.md). **LLM routing:** [SKILLS.md](../../SKILLS.md) → then these docs for depth.

Conventions for humans and **LLM / agent** contributors. **[ARCHITECTURE.md](ARCHITECTURE.md)** describes package layout and data flow in more detail.

## Naming

| Kind | Convention | Examples |
|------|------------|----------|
| **Public functions** (re-exported from `polymwk`) | `camelCase` | `fetchEvents()`, `fetchUserInfo()`, `displayUserPositions()` |
| **`subscribe*` (streaming, **feed only**) | **`subscribe<Module><Action>`** (`camelCase`; mirror related **`fetch*`** inner caps when paired) | `subscribeMarketOrderBook()` ↔ `fetchOrderBook()` |
| **Variables & parameters** | `snake_case` | `market_slug`, `max_results`, `include_stats` |
| **Constants** | `UPPER_SNAKE` | `DEFAULT_EVENT_LIMIT`, module-level `_MAX_ACTIVITY_PAGE` in thin entry files |
| **Classes / models** | `PascalCase` | `Event`, `UserInfo`, `UserClosedPosition` |
| **Type aliases** (exported when useful) | `PascalCase` | `UserPositionsStatus` |
| **Private helpers** (`_internal/`, package `utils.py`) | `snake_case` | `resolve_user_to_proxy_wallet()`, `trade_from_data_api()` |

Public **camelCase** vs internal **snake_case** makes it obvious what is user-facing. **REST-style pulls** use **`fetch*`** (`events/`, `users/`, …). **Live WebSocket / streaming** is **entirely** under **`feed/`**: only there do we add **`subscribe*`** — never `subscribe*` in `events/`, `users/`, or `displays/`.

## Package layout

- **`polymwk/__init__.py`** — Imports and `__all__` only. No loops, no function bodies, no non-trivial logic.
- **`main.py`** (project root) — End-user script style: imports + direct calls. **No** `if __name__ == "__main__":`, **no** `def`, **no** loops — the same code you would paste into a REPL.
- **`main.py` call style** — **One line per call**, **keyword arguments**. Good: `displayEvents(events, tags="nvda", show_markets=True)`. Bad: hanging multi-line argument lists wrapped only for wrapping.
- **`polymwk/utils/`** — Cross-package helpers (tag query normalization, slug helpers). Do **not** put domain-specific Data API mapping here; that belongs in the domain package’s **`utils.py`** (e.g. `users/utils.py`).

### Per-package `utils.py`

- **`events/utils.py`**, **`displays/utils.py`**, **`users/utils.py`**, etc. hold **non-exported** helpers (`snake_case`).
- **Entry modules stay thin**: e.g. `users/info.py` only `fetchUserInfo`; `users/activity.py` only `fetchUserActivity`; mapping and resolution live in **`users/utils.py`**.
- Add a local **`utils.py`** when a package accumulates shared helpers; **do not** create empty `utils.py` files.

### Users package (`polymwk/users/`) — file roles

| File | Role |
|------|------|
| **`info.py`** | `fetchUserInfo` — Gamma public profile + optional Data API stats |
| **`activity.py`** | `fetchUserActivity` — paginated `GET /activity` |
| **`trades.py`** | `fetchUserTrades` — paginated `GET /trades` |
| **`positions.py`** | `fetchUserPositions` — `GET /positions` (active) or `GET /closed-positions` (closed); `UserPositionsStatus` |
| **`leaderboard.py`** | `fetchUserLeaderboardRank` (`lb-api`); `fetchUsersLeaderboard` (`/v1/leaderboard`, timeframe + category); metric/window/timeframe/category type aliases |
| **`utils.py`** | Handle → proxy, profile/stats, activity/trades/positions/leaderboard mapping to `polymwk.models` |
| **`models.py`**, **`holders.py`**, **`pnl.py`** | Scaffolds / reserved; prefer expanding real modules before growing unused shells |

When adding a **new user-facing fetch**, add a small **`users/<topic>.py`** with the `camelCase` function and put **vendor → model** mapping in **`users/utils.py`**.

### Feed package (`polymwk/feed/`) — all streaming / WebSocket

- **Scope:** Everything we build for live streams goes **here** — thin **`feed/<topic>.py`** files, **`feed/utils.py`** for shared feed logic, **`feed/models.py`** if feed-specific DTOs are needed. Root **`polymwk/__init__.py`** re-exports **`subscribe*`** from **`feed/__init__.py`** like other subpackages.
- **Naming:** **`subscribe<Module><Action>`** only (see Naming table). **`events/`** keeps **`fetch*`** snapshots only (e.g. `fetchOrderBook`); the streaming twin lives in **`feed/`** (e.g. `subscribeMarketOrderBook`).
- **`_internal/websockets.py`** (or similar) is **non-public** glue **used by** `feed/` if needed — not a second place to define **`subscribe*`**.

### Displays package (`polymwk/displays/`)

- **Layout:** **`displays/events/`** (market / Gamma / CLOB snapshot views), **`displays/users/`**, **`displays/feed/`** (views that drive off **`polymwk.feed`** streaming, e.g. **`displayLiveOrderBook`**), **`displays/history/`** (scaffold). Shared **`displays/utils.py`** stays at the package root — **not** inside subfolders.
- One **`display*.py`** (or focused module name) per major fetch/stream family under the matching subfolder. **`displayEvents`** lives in **`events/listing.py`** so the package can be named **`displays.events`** without clashing with a top-level **`events.py`**.
- Reuse **`displays/utils.py`** (`term_width`, `emit_boxed_header`, `format_display_num`, wrapping, colors).
- **Boxed header pattern** (`emit_boxed_header`): kind line + subtitle (slug, wallet, status, counts) for consistent terminal chrome.

## Behaviour

- **Discovery** uses **market/event slugs** on the public surface; **condition IDs** stay inside **`_internal/`** and mapping layers unless a function is explicitly low-level.
- **Public functions return polymwk `models`** (Pydantic), not raw vendor types or client instances.
- **HTTP / vendor failures** → wrap in **`PolymwkApiError`** (or **`PolymwkError`**) where appropriate; preserve **`from exc`** chaining.
- **Pagination & caps** — Many Data API methods cap `limit` (e.g. 500). Document in docstrings; clamp in code; prefer **one HTTP call per public function** unless a dedicated “fetch all pages” helper is explicitly requested (then add delays / batching guidance in docs).

## Future direction (for contributors)

- **`events/search.py`**, fuller **`fetchMarkets`** — discovery polish.
- **`users/pnl.py`** — explicit PnL series (`get_pnl`) / leaderboard helpers if needed without overloading **`fetchUserInfo`**.
- **`history/`** — candles, archives; keep public API camelCase when exposed.
- **`feed/`** — WebSocket / live streams; public **`subscribe*`** entrypoints (see Feed package above).
- **Tests** — Mirror package layout under `tests/`; mock `get_data_client` / `get_gamma_client` at the module under test.

## LLM quick checklist

1. **New fetch** → thin `*.py` in the right package + mapping in that package’s **`utils.py`** + **`PolymwkApiError`/`PolymwkError`** + test with **`unittest.mock.patch`** on the client getter used in that module.
2. **New model fields** → **`models.py`**; keep **`extra="ignore"`** on public DTOs; default new fields when extending existing models so old dicts still validate if needed.
3. **New display** → thin module under **`displays/events/`**, **`displays/users/`**, **`displays/feed/`**, or **`displays/history/`** (match the data source) + that subfolder’s **`__init__.py`** + root **`displays/__init__.py`** + **`polymwk/__init__.py`** `__all__` + **`ARCHITECTURE.md`** map line.
4. **New streaming API** → **only** under **`feed/`**: `subscribe<Module><Action>` in thin **`feed/*.py`**, helpers in **`feed/utils.py`**, **`feed/__init__.py`** + root **`polymwk/__init__.py`** `__all__` + **`ARCHITECTURE.md`**; do not add **`subscribe*`** outside **`feed/`**.
5. **Docs** — Update **`ARCHITECTURE.md`** when adding packages or major flows; keep **`RULES.md`** aligned with naming and layout.
