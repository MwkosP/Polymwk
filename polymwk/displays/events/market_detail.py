"""Compact terminal view for a single :class:`~polymwk.models.Market`."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import Market
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    format_display_num,
    format_vol_24h,
    term_style,
    term_width,
)


def displayMarket(
    market: Market,
    *,
    event_title: str = "",
    stream: TextIO | None = None,
) -> None:
    """
    Short summary: question, slug, internal ids (when present), Yes/No prices,
    liquidity, volumes, optional parent event title.
    """
    out = stream if stream is not None else sys.stdout
    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)

    if not isinstance(market, Market):
        raise PolymwkError("displayMarket expects polymwk.models.Market")

    sub = clip_text(market.question, 62) if market.question else (market.slug or "Market")
    emit_boxed_header(
        out,
        lines=(f"{bold}Market{rst}", f"{accent}{sub}{rst}"),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    if event_title.strip():
        out.write(f"  {dim}event{rst} {clip_text(event_title.strip(), 80)}\n")

    out.write(f"  {dim}slug{rst} {market.slug or '—'}\n")
    if market.internal_id:
        out.write(f"  {dim}id{rst} {market.internal_id}\n")
    if market.condition_id:
        out.write(f"  {dim}condition_id{rst} {clip_text(market.condition_id, 72)}\n")

    st = f"{accent}● active{rst}" if market.active else f"{dim}○ inactive{rst}"
    out.write(f"  {st}\n")

    out.write(
        f"  {dim}Yes / No{rst} {market.yes_price:.4f} {dim}/{rst} {market.no_price:.4f}\n"
    )
    vol = format_display_num(market.volume)
    v24 = format_vol_24h(market.volume_24h)
    liq = format_display_num(market.liquidity)
    out.write(f"  {dim}volume{rst} {vol}  {dim}24h{rst} {v24}  {dim}liq{rst} {liq}\n")

    if market.end_date:
        out.write(f"  {dim}ends{rst} {market.end_date.isoformat()}\n")

    if market.yes_token_id:
        out.write(
            f"\n  {dim}yes_token_id{rst} {clip_text(market.yes_token_id, 64)}\n"
        )
    if market.no_token_id:
        out.write(f"  {dim}no_token_id{rst} {clip_text(market.no_token_id, 64)}\n")

    out.write("\n")
