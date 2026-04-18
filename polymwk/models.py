"""Shared Pydantic v2 models — public fields only."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Tag(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str | None = None
    label: str | None = None


class TagsConfigEntry(BaseModel):
    """One subgroup under :class:`TagsConfigCategory` (e.g. ``all``, ``bitcoin``)."""

    model_config = ConfigDict(extra="ignore")

    slug: str
    keywords: list[str] = Field(default_factory=list)


class TagsConfigCategory(BaseModel):
    """A top-level config bucket (e.g. ``crypto``, ``geopolitics``)."""

    model_config = ConfigDict(extra="ignore")

    slug: str
    entries: list[TagsConfigEntry] = Field(default_factory=list)


class TagsConfigSnapshot(BaseModel):
    """Keyword tree from :mod:`polymwk.configs.tags` for inspection / display."""

    model_config = ConfigDict(extra="ignore")

    categories: list[TagsConfigCategory] = Field(default_factory=list)
    source: str = "polymwk.configs.tags"


class Market(BaseModel):
    model_config = ConfigDict(extra="ignore")

    slug: str
    question: str
    yes_price: float = Field(ge=0.0, le=1.0)
    no_price: float = Field(ge=0.0, le=1.0)
    yes_token_id: str = ""
    no_token_id: str = ""
    internal_id: str = ""
    condition_id: str = ""
    volume: float = 0.0
    volume_24h: float | None = None
    liquidity: float = 0.0
    end_date: datetime | None = None
    active: bool = True


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    title: str
    description: str = ""
    markets: list[Market] = Field(default_factory=list)
    market_count: int = 0
    volume: float = 0.0
    volume_24h: float | None = None
    active: bool = True
    end_date: datetime | None = None
    primary_yes_price: float | None = Field(default=None, ge=0.0, le=1.0)
    primary_no_price: float | None = Field(default=None, ge=0.0, le=1.0)


class Series(BaseModel):
    """Recurring / grouped market series from Gamma (discovered via tagged events)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    title: str
    subtitle: str = ""
    series_type: str = ""
    recurrence: str = ""
    description: str = ""
    active: bool = True
    closed: bool = False
    archived: bool = False
    volume: float = 0.0
    volume_24h: float | None = None
    liquidity: float = 0.0
    event_count: int = 0


class BookLevel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    price: float
    size: float


class OrderBook(BaseModel):
    model_config = ConfigDict(extra="ignore")

    market_slug: str
    best_bid: float
    best_ask: float
    spread: float
    midpoint: float
    bids: list[BookLevel] = Field(default_factory=list)
    asks: list[BookLevel] = Field(default_factory=list)
    timestamp: datetime


class Trade(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wallet: str
    market_slug: str
    market_title: str
    side: str
    outcome: str
    price: float
    size: float
    value_usd: float
    timestamp: datetime
    tx_hash: str


class HistoricalTrade(BaseModel):
    model_config = ConfigDict(extra="ignore")

    market_slug: str
    side: str
    outcome: str
    price: float
    size: float
    timestamp: datetime
    tx_hash: str | None = None


class Position(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wallet: str
    market_slug: str
    market_title: str
    outcome: str
    size: float
    avg_price: float
    current_price: float
    current_value: float
    unrealised_pnl: float
    realised_pnl: float


class UserClosedPosition(BaseModel):
    """One resolved / closed row from Data API ``GET /closed-positions``."""

    model_config = ConfigDict(extra="ignore")

    wallet: str
    market_slug: str
    market_title: str
    outcome: str
    avg_price: float
    current_price: float
    total_bought: float
    realized_pnl: float
    closed_at: datetime | None = None
    condition_id: str = ""


class PnL(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wallet: str
    period: str
    realised_pnl: float
    unrealised_pnl: float
    total_pnl: float
    total_volume: float
    win_rate: float | None = None


class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wallet: str
    type: str
    timestamp: datetime | None = None
    market_slug: str | None = None
    detail: str | None = None
    # From Data API ``GET /activity`` (defaults keep older 4-field payloads valid)
    market_title: str = ""
    outcome: str = ""
    side: str | None = None
    size: float = 0.0
    usdc_size: float = 0.0
    price: float = 0.0
    condition_id: str = ""
    transaction_hash: str = ""
    event_slug: str = ""


class Candle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class PricePoint(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    price: float


class Holder(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wallet: str
    outcome: str
    size: float
    avg_price: float
    value_usd: float


class MarketTopHolder(BaseModel):
    """One row from Data API ``/holders`` for an outcome token."""

    model_config = ConfigDict(extra="ignore")

    wallet: str
    size: float
    outcome_index: int
    token_id: str = ""
    name: str = ""
    pseudonym: str = ""


class MarketTopHoldersGroup(BaseModel):
    """Top holders for a single outcome token (e.g. Yes vs No)."""

    model_config = ConfigDict(extra="ignore")

    token_id: str
    outcome_label: str
    holders: list[MarketTopHolder] = Field(default_factory=list)


class MarketTopHoldersSnapshot(BaseModel):
    """Per-market holder ladder from ``fetchMarketTopHolders``."""

    model_config = ConfigDict(extra="ignore")

    market_slug: str
    condition_id: str
    event_slug: str = ""
    groups: list[MarketTopHoldersGroup] = Field(default_factory=list)


class MarketUserPosition(BaseModel):
    """One row from Data API ``/v1/market-positions`` (site PnL table)."""

    model_config = ConfigDict(extra="ignore")

    wallet: str
    display_name: str
    outcome: str
    outcome_index: int = 0
    avg_price: float = 0.0
    total_pnl: float = 0.0
    cash_pnl: float = 0.0
    current_value: float = 0.0
    token_id: str = ""


class MarketUsersPositionsGroup(BaseModel):
    """Positions for one outcome token, sorted like the UI."""

    model_config = ConfigDict(extra="ignore")

    token_id: str
    outcome_label: str
    positions: list[MarketUserPosition] = Field(default_factory=list)


class MarketUsersPositionsSnapshot(BaseModel):
    """Per-market, all users’ positions from ``fetchMarketUsersPositions``."""

    model_config = ConfigDict(extra="ignore")

    market_slug: str
    condition_id: str
    event_slug: str = ""
    groups: list[MarketUsersPositionsGroup] = Field(default_factory=list)


class MarketLastActivityRow(BaseModel):
    """One taker trade row from Data API ``/trades`` for a condition."""

    model_config = ConfigDict(extra="ignore")

    wallet: str
    display_name: str
    side: str
    size: float
    price: float
    outcome: str
    value_usd: float
    timestamp: datetime
    transaction_hash: str = ""


class MarketLastActivitySnapshot(BaseModel):
    """Newest-first trade feed for one market from ``fetchMarketLastActivity``."""

    model_config = ConfigDict(extra="ignore")

    market_slug: str
    condition_id: str
    event_slug: str = ""
    activities: list[MarketLastActivityRow] = Field(default_factory=list)


class EventCommentRow(BaseModel):
    """One Gamma comment on an event (thread / reply)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    body: str
    user_address: str
    display_name: str
    created_at: datetime
    parent_comment_id: str | None = None
    reply_to_address: str | None = None
    reaction_count: int = 0


class EventCommentsSnapshot(BaseModel):
    """Comments for one event from ``fetchEventComments``."""

    model_config = ConfigDict(extra="ignore")

    event_id: int
    event_slug: str
    event_title: str = ""
    comments: list[EventCommentRow] = Field(default_factory=list)


class MarketPricePoint(BaseModel):
    """One CLOB ``/prices-history`` sample (implied probability for the token)."""

    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    price: float


class MarketPricesSnapshot(BaseModel):
    """Yes/No token price history for one market from ``fetchMarketPrices``."""

    model_config = ConfigDict(extra="ignore")

    market_slug: str
    token_id: str
    outcome_label: str
    interval: str
    fidelity: int
    event_slug: str = ""
    points: list[MarketPricePoint] = Field(default_factory=list)


class MarketRulesSnapshot(BaseModel):
    """Resolution rules copy for one market from Gamma (``/markets/slug/…``)."""

    model_config = ConfigDict(extra="ignore")

    market_slug: str
    market_question: str = ""
    event_slug: str = ""
    event_title: str = ""
    rules_body: str = ""
    event_description: str = ""
    resolution_source: str = ""
    uma_resolution_status: str | None = None


class UserIdentity(BaseModel):
    """Subset of Gamma profile-linked account flags."""

    model_config = ConfigDict(extra="ignore")

    id: str
    creator: bool = False
    mod: bool = False
    community_mod: bool | None = None


class UserInfo(BaseModel):
    """Public Polymarket profile from Gamma ``/public-profile`` (by proxy wallet)."""

    model_config = ConfigDict(extra="ignore")

    proxy_wallet: str
    pseudonym: str = ""
    name: str | None = None
    bio: str | None = None
    profile_image: str | None = None
    created_at: datetime | None = None
    display_username_public: bool = True
    x_username: str | None = None
    verified_badge: bool = False
    profile_slug: str = ""
    profile_url: str = ""
    query: str = ""
    identities: list[UserIdentity] = Field(default_factory=list)
    # Data API enrichments (see ``fetchUserInfo(..., include_stats=True)``)
    positions_value_usd: float | None = None
    biggest_win_usd: float | None = None
    markets_traded: int | None = None
    profit_loss_all_usd: float | None = None
    pnl_history: list[float] = Field(
        default_factory=list,
        description="All-time PnL samples (e.g. daily) for sparkline display.",
    )


class UserLeaderboardRank(BaseModel):
    """Leaderboard rank from ``lb-api`` for one metric/window, plus optional cross-stat."""

    model_config = ConfigDict(extra="ignore")

    proxy_wallet: str
    rank: int
    metric: Literal["profit", "volume"]
    window: Literal["1d", "7d", "30d", "all"]
    ranked_amount: float
    other_metric_amount: float | None = None
    name: str = ""
    pseudonym: str = ""
    bio: str = ""
    profile_image: str = ""


class LeaderboardEntry(BaseModel):
    """One row from Data API ``GET /v1/leaderboard`` (profit + volume for that window/category)."""

    model_config = ConfigDict(extra="ignore")

    rank: int
    proxy_wallet: str
    username: str = ""
    pnl: float = 0.0
    volume_usd: float = 0.0
    profile_image: str = ""
    verified_badge: bool = False


class UsersLeaderboardSnapshot(BaseModel):
    """Top traders for a timeframe/category (Polymarket leaderboard UI)."""

    model_config = ConfigDict(extra="ignore")

    timeframe: Literal["today", "weekly", "monthly", "all"]
    category: str
    category_label: str = ""
    order_by: Literal["pnl", "vol"]
    entries: list[LeaderboardEntry] = Field(default_factory=list)


class MarketResolutionSnapshot(BaseModel):
    """Gamma market resolution / UMA metadata (``/markets/slug/…``) — no on-chain UMA."""

    model_config = ConfigDict(extra="ignore")

    market_slug: str
    market_question: str = ""
    event_slug: str = ""
    event_title: str = ""
    condition_id: str = ""
    question_id: str = ""
    resolution_source: str = ""
    closed: bool | None = None
    archived: bool | None = None
    active: bool | None = None
    closed_time: str = ""
    resolved_by: str = ""
    uma_resolution_status: str | None = None
    uma_end_date: datetime | None = None
    uma_end_date_iso: datetime | None = None
    uma_bond: str = ""
    uma_reward: str = ""


class OrderBookUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    market_slug: str
    best_bid: float | None = None
    best_ask: float | None = None
    timestamp: datetime | None = None


class TradeEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    market_slug: str
    price: float
    size: float
    side: str
    timestamp: datetime | None = None
