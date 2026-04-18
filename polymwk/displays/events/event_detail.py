"""Compact terminal view for a single :class:`~polymwk.models.Event`."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import Event
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    format_display_num,
    format_vol_24h,
    term_style,
    term_width,
)


def displayEvent(
    event: Event,
    *,
    stream: TextIO | None = None,
    max_description_lines: int = 3,
) -> None:
    """
    Short summary: title, ids, status, volumes, end date, optional description,
    and a one-line hint per embedded market (slug · Yes/No).
    """
    out = stream if stream is not None else sys.stdout
    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)

    if not isinstance(event, Event):
        raise PolymwkError("displayEvent expects polymwk.models.Event")

    emit_boxed_header(
        out,
        lines=(f"{bold}Event{rst}", f"{accent}{clip_text(event.title, 64)}{rst}"),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    out.write(f"  {dim}id{rst} {event.id}  {dim}slug{rst} {event.slug or '—'}\n")
    st = f"{accent}● active{rst}" if event.active else f"{dim}○ inactive{rst}"
    out.write(f"  {st}\n")
    vol = format_display_num(event.volume)
    v24 = format_vol_24h(event.volume_24h)
    out.write(f"  {dim}volume{rst} {vol}  {dim}24h{rst} {v24}\n")
    if event.end_date:
        out.write(f"  {dim}ends{rst} {event.end_date.isoformat()}\n")

    if event.description.strip():
        desc = event.description.replace("\n", " ").strip()
        out.write(f"\n  {dim}description{rst}\n")
        cap = max(40, min(96, term_w - 6))
        chunk = desc[: cap * max_description_lines]
        if len(desc) > len(chunk):
            chunk = chunk.rstrip() + "…"
        out.write(f"  {dim}{clip_text(chunk, cap * max_description_lines + 3)}{rst}\n")

    if event.markets:
        out.write(f"\n  {dim}markets ({len(event.markets)}){rst}\n")
        inner = max(36, min(term_w - 6, 90))
        for m in event.markets[:20]:
            emit_horizontal_rule(out, inner, dim=dim, rst=rst, label=None)
            y = m.yes_price
            n = m.no_price
            out.write(
                f"  {clip_text(m.question, 72)}\n"
                f"  {dim}slug{rst} {m.slug}  {dim}Yes/No{rst} {y:.2f} / {n:.2f}\n"
            )
        if len(event.markets) > 20:
            out.write(f"  {dim}… {len(event.markets) - 20} more{rst}\n")
    else:
        out.write(f"\n  {dim}(markets not loaded — use fetchEvent with get_markets=True){rst}\n")

    out.write("\n")
