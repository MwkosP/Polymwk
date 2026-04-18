# polymwk — LLM / agent skill (routing)

Use this file as the **first stop** when helping with this repository. Deep detail lives under **`assets/docs/`**.

## Read next (in order)

| Doc | Path | Use when |
|-----|------|----------|
| **Usage** | [assets/docs/USAGE.md](assets/docs/USAGE.md) | Which `fetch*` / `display*` / `subscribe*` exist, params, returns, short examples. |
| **Architecture** | [assets/docs/ARCHITECTURE.md](assets/docs/ARCHITECTURE.md) | Package layout, Gamma / CLOB / Data API, export map. |
| **Rules** | [assets/docs/RULES.md](assets/docs/RULES.md) | Naming (`fetch*` / `display*` / `subscribe*`), `main.py`, where to add code, checklist. |

## Conventions (summary)

- Import from **`polymwk`**: `from polymwk import fetchEvents, displayEvents, …` (see `polymwk/__init__.py` `__all__`).
- **camelCase** public functions; **`fetch*`** = HTTP snapshots, **`subscribe*`** = live feed (`polymwk/feed/`), **`display*`** = terminal output (`None` return).
- Errors: **`PolymwkError`** (validation), **`PolymwkApiError`** (upstream HTTP).

## If the user is stuck

1. Open **[USAGE.md](assets/docs/USAGE.md)** for the specific API.
2. Open **[ARCHITECTURE.md](assets/docs/ARCHITECTURE.md)** to find the owning module.
3. Open **[RULES.md](assets/docs/RULES.md)** before adding or renaming exports.

Do not treat `polymwk/_internal/` as a stable public surface unless the user explicitly wants low-level access.
