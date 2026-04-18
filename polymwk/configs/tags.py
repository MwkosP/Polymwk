"""
Keyword lists for coarse tagging / query expansion (crypto, geopolitics, etc.).

Subcategories use short names (e.g. BITCOIN). Each major category (CRYPTO, …) is the
union of all keywords from its subcategories (order preserved, duplicates removed).
"""

from __future__ import annotations
from typing import Final
from polymwk.models import TagsConfigCategory, TagsConfigEntry, TagsConfigSnapshot


def _merge_unique(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for g in groups:
        for w in g:
            if w not in seen:
                seen.add(w)
                out.append(w)
    return out


# =============================================================================
# CRYPTO
# =============================================================================

# --- Bitcoin ---
BITCOIN: Final[list[str]] = [
    "bitcoin",
    "btc",
]

# --- Ethereum ---
ETHEREUM: Final[list[str]] = [
    "ethereum",
    "eth",
    "erc-20",
    "erc20",
]

# --- Altcoins & L1/L2 ---
ALTCOINS: Final[list[str]] = [
    "altcoin",
    "solana",
    "sol",
    "cardano",
    "ada",
    "avalanche",
    "avax",
    "polygon",
    "matic",
    "arbitrum",
    "optimism",
    "base chain",
]

# --- DeFi & stablecoins ---
DEFI: Final[list[str]] = [
    "defi",
    "dex",
    "amm",
    "liquidity pool",
    "yield",
    "stablecoin",
    "usdt",
    "usdc",
    "dai",
    "tether",
]

# --- Regulation & ETFs ---
REGULATION: Final[list[str]] = [
    "sec",
    "etf",
    "spot etf",
    "crypto regulation",
    "ban",
    "custody",
]

CRYPTO: Final[list[str]] = _merge_unique(
    BITCOIN, ETHEREUM, ALTCOINS, DEFI, REGULATION
)

# =============================================================================
# GEOPOLITICS
# =============================================================================

# --- Elections & governance ---
ELECTIONS: Final[list[str]] = [
    "election",
    "presidential",
    "parliament",
    "referendum",
    "senate",
    "congress",
    "prime minister",
    "chancellor",
]

# --- Conflict & security ---
CONFLICT: Final[list[str]] = [
    "war",
    "ceasefire",
    "nato",
    "sanctions",
    "invasion",
    "military",
    "peace talks",
]

# --- Regions ---
UKRAINE: Final[list[str]] = [
    "ukraine",
    "kyiv",
    "kiev",
    "zelensky",
    "crimea",
    "donbas",
]

MIDDLE_EAST: Final[list[str]] = [
    "israel",
    "gaza",
    "iran",
    "saudi",
    "yemen",
    "hezbollah",
    "middle east",
]

ASIA_PACIFIC: Final[list[str]] = [
    "taiwan",
    "south china sea",
    "north korea",
    "kim jong",
    "ccp",
    "xi jinping",
]

GEOPOLITICS: Final[list[str]] = _merge_unique(
    ELECTIONS, CONFLICT, UKRAINE, MIDDLE_EAST, ASIA_PACIFIC
)

# =============================================================================
# ECONOMICS & MACRO
# =============================================================================

# --- Central banks & rates ---
FED_RATES: Final[list[str]] = [
    "fed",
    "federal reserve",
    "fomc",
    "interest rate",
    "rate cut",
    "rate hike",
    "powell",
]

INFLATION_GROWTH: Final[list[str]] = [
    "inflation",
    "cpi",
    "ppi",
    "gdp",
    "recession",
    "unemployment",
    "jobs report",
]

ECONOMICS: Final[list[str]] = _merge_unique(FED_RATES, INFLATION_GROWTH)

# =============================================================================
# SPORTS
# =============================================================================

NFL: Final[list[str]] = [
    "nfl",
    "super bowl",
    "touchdown",
    "quarterback",
]

NBA: Final[list[str]] = [
    "nba",
    "basketball",
    "playoffs",
    "finals mvp",
]

SOCCER: Final[list[str]] = [
    "premier league",
    "champions league",
    "world cup",
    "la liga",
    "bundesliga",
]

SPORTS: Final[list[str]] = _merge_unique(NFL, NBA, SOCCER)

# =============================================================================
# SCIENCE & TECH (non-crypto)
# =============================================================================

AI: Final[list[str]] = [
    "openai",
    "chatgpt",
    "anthropic",
    "gemini",
    "llm",
    "artificial intelligence",
    "agi",
]

SPACE: Final[list[str]] = [
    "spacex",
    "nasa",
    "starship",
    "mars mission",
    "rocket launch",
]

SCIENCE_TECH: Final[list[str]] = _merge_unique(AI, SPACE)

# =============================================================================
# Tree: each category has "all" (full rollup) plus subcategory lists
# =============================================================================

TAG_TREE: Final[dict[str, dict[str, list[str]]]] = {
    "crypto": {
        "all": CRYPTO,
        "bitcoin": BITCOIN,
        "ethereum": ETHEREUM,
        "altcoins": ALTCOINS,
        "defi": DEFI,
        "regulation": REGULATION,
    },
    "geopolitics": {
        "all": GEOPOLITICS,
        "elections": ELECTIONS,
        "conflict": CONFLICT,
        "ukraine": UKRAINE,
        "middle_east": MIDDLE_EAST,
        "asia_pacific": ASIA_PACIFIC,
    },
    "economics": {
        "all": ECONOMICS,
        "fed_rates": FED_RATES,
        "inflation_growth": INFLATION_GROWTH,
    },
    "sports": {
        "all": SPORTS,
        "nfl": NFL,
        "nba": NBA,
        "soccer": SOCCER,
    },
    "science_tech": {
        "all": SCIENCE_TECH,
        "ai": AI,
        "space": SPACE,
    },
}


def _ordered_tag_entries(
    sub: dict[str, list[str]],
) -> list[tuple[str, list[str]]]:
    """``all`` first, then remaining keys sorted for stable output."""
    out: list[tuple[str, list[str]]] = []
    if "all" in sub:
        out.append(("all", list(sub["all"])))
    for key in sorted(k for k in sub if k != "all"):
        out.append((key, list(sub[key])))
    return out


def fetchTags() -> TagsConfigSnapshot:
    """
    Load the **keyword tag tree** from this module (no network).

    Returns a snapshot of :data:`TAG_TREE`: each category (``crypto``, …) and its
    sub-keys (``all``, ``bitcoin``, …) with the search keyword lists used for
    coarse matching / query expansion when you edit :mod:`polymwk.configs.tags`.
    """
    categories: list[TagsConfigCategory] = []
    for cat_slug in sorted(TAG_TREE.keys()):
        sub = TAG_TREE[cat_slug]
        entries = [
            TagsConfigEntry(slug=slug, keywords=list(kws))
            for slug, kws in _ordered_tag_entries(sub)
        ]
        categories.append(TagsConfigCategory(slug=cat_slug, entries=entries))
    return TagsConfigSnapshot(categories=categories)
