"""Compact terminal view for a single :class:`~polymwk.models.Series`."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import Series
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    format_display_num,
    format_vol_24h,
    term_style,
    term_width,
)


def displaySerie(
    serie: Series,
    *,
    stream: TextIO | None = None,
) -> None:
    """
    Short summary for one series: title, slug, id, recurrence, status, volumes, liquidity.
    """
    out = stream if stream is not None else sys.stdout
    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)

    if not isinstance(serie, Series):
        raise PolymwkError("displaySerie expects polymwk.models.Series")

    emit_boxed_header(
        out,
        lines=(f"{bold}Series{rst}", f"{accent}{clip_text(serie.title, 64)}{rst}"),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    out.write(f"  {dim}id{rst} {serie.id or '—'}  {dim}slug{rst} {serie.slug or '—'}\n")
    if serie.subtitle:
        out.write(f"  {dim}subtitle{rst} {clip_text(serie.subtitle, 90)}\n")
    meta = [p for p in (serie.series_type, serie.recurrence) if p.strip()]
    if meta:
        out.write(f"  {dim}{' · '.join(meta)}{rst}\n")

    st = (
        f"{accent}● active{rst}"
        if serie.active and not serie.closed
        else f"{dim}○ closed / inactive{rst}"
    )
    out.write(f"  {st}\n")

    vol = format_display_num(serie.volume)
    v24 = format_vol_24h(serie.volume_24h)
    liq = format_display_num(serie.liquidity)
    out.write(f"  {dim}volume{rst} {vol}  {dim}24h{rst} {v24}  {dim}liq{rst} {liq}\n")
    if serie.event_count:
        out.write(f"  {dim}events (tag scan count){rst} {serie.event_count}\n")

    if serie.description.strip():
        out.write(f"\n  {dim}{clip_text(serie.description.replace(chr(10), ' '), 120)}{rst}\n")

    out.write("\n")
