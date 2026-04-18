"""Map raw vendor payloads into polymwk models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from polymwk.exceptions import PolymwkError
from polymwk.models import (
    Activity,
    BookLevel,
    Candle,
    Event,
    HistoricalTrade,
    Holder,
    Market,
    OrderBook,
    OrderBookUpdate,
    PnL,
    Position,
    PricePoint,
    Tag,
    Trade,
    TradeEvent,
)


def _validate[T](model_cls: type[T], raw: Mapping[str, Any] | Any) -> T:
    try:
        return model_cls.model_validate(raw)
    except ValidationError as exc:
        raise PolymwkError(f"{model_cls.__name__} validation failed") from exc


def to_tag(raw: Any) -> Tag:
    if isinstance(raw, Tag):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Tag, raw)
    raise PolymwkError("to_tag expects a mapping or Tag")


def to_market(raw: Any) -> Market:
    if isinstance(raw, Market):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Market, raw)
    raise PolymwkError("to_market expects a mapping or Market")


def to_event(raw: Any) -> Event:
    if isinstance(raw, Event):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Event, raw)
    raise PolymwkError("to_event expects a mapping or Event")


def to_order_book(raw: Any) -> OrderBook:
    if isinstance(raw, OrderBook):
        return raw
    if isinstance(raw, Mapping):
        return _validate(OrderBook, raw)
    raise PolymwkError("to_order_book expects a mapping or OrderBook")


def to_book_level(raw: Any) -> BookLevel:
    if isinstance(raw, BookLevel):
        return raw
    if isinstance(raw, Mapping):
        return _validate(BookLevel, raw)
    raise PolymwkError("to_book_level expects a mapping or BookLevel")


def to_trade(raw: Any) -> Trade:
    if isinstance(raw, Trade):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Trade, raw)
    raise PolymwkError("to_trade expects a mapping or Trade")


def to_historical_trade(raw: Any) -> HistoricalTrade:
    if isinstance(raw, HistoricalTrade):
        return raw
    if isinstance(raw, Mapping):
        return _validate(HistoricalTrade, raw)
    raise PolymwkError("to_historical_trade expects a mapping or HistoricalTrade")


def to_position(raw: Any) -> Position:
    if isinstance(raw, Position):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Position, raw)
    raise PolymwkError("to_position expects a mapping or Position")


def to_pnl(raw: Any) -> PnL:
    if isinstance(raw, PnL):
        return raw
    if isinstance(raw, Mapping):
        return _validate(PnL, raw)
    raise PolymwkError("to_pnl expects a mapping or PnL")


def to_activity(raw: Any) -> Activity:
    if isinstance(raw, Activity):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Activity, raw)
    raise PolymwkError("to_activity expects a mapping or Activity")


def to_candle(raw: Any) -> Candle:
    if isinstance(raw, Candle):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Candle, raw)
    raise PolymwkError("to_candle expects a mapping or Candle")


def to_price_point(raw: Any) -> PricePoint:
    if isinstance(raw, PricePoint):
        return raw
    if isinstance(raw, Mapping):
        return _validate(PricePoint, raw)
    raise PolymwkError("to_price_point expects a mapping or PricePoint")


def to_holder(raw: Any) -> Holder:
    if isinstance(raw, Holder):
        return raw
    if isinstance(raw, Mapping):
        return _validate(Holder, raw)
    raise PolymwkError("to_holder expects a mapping or Holder")


def to_order_book_update(raw: Any) -> OrderBookUpdate:
    if isinstance(raw, OrderBookUpdate):
        return raw
    if isinstance(raw, Mapping):
        return _validate(OrderBookUpdate, raw)
    raise PolymwkError("to_order_book_update expects a mapping or OrderBookUpdate")


def to_trade_event(raw: Any) -> TradeEvent:
    if isinstance(raw, TradeEvent):
        return raw
    if isinstance(raw, Mapping):
        return _validate(TradeEvent, raw)
    raise PolymwkError("to_trade_event expects a mapping or TradeEvent")
