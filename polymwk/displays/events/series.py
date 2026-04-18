"""Print polymwk :class:`~polymwk.models.Series` rows."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import Series
from polymwk.displays.utils import (
    center_line,
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    format_display_num,
    format_vol_24h,
    term_style,
    term_width,
)


def displaySeries(
    series: Series | Sequence[Series],
    *,
    tags: str | Sequence[str] | None = None,
    stream: TextIO | None = None,
    max_subtitle_len: int = 120,
) -> None:
    """
    Pretty-print one or more :class:`~polymwk.models.Series` (title, slug, recurrence,
    volumes, and how many matching events contributed to discovery).
    """
    out = stream if stream is not None else sys.stdout
    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)

    if isinstance(tags, str):
        tag_line = tags.strip()
    elif tags is not None:
        tag_line = ", ".join(t.strip() for t in tags if str(t).strip())
    else:
        tag_line = ""

    line_sub = (
        f"{accent}Series for {tag_line}{rst}"
        if tag_line
        else f"{accent}Series{rst}"
    )
    emit_boxed_header(
        out,
        lines=(f"{bold}Display{rst}", line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    rows: list[Series] = [series] if isinstance(series, Series) else list(series)
    if not rows:
        center_line(out, f"{dim}(no series){rst}", term_w)
        out.write("\n")
        return

    inner_w = max(40, min(term_w - 4, 100))

    for i, s in enumerate(rows, start=1):
        if not isinstance(s, Series):
            raise PolymwkError("displaySeries expects polymwk.models.Series instances")

        emit_horizontal_rule(
            out,
            inner_w,
            dim=dim,
            rst=rst,
            label=f"{i} / {len(rows)}",
        )

        out.write(f"  {bold}{clip_text(s.title, 72)}{rst}\n")
        out.write(f"  {dim}slug{rst} {s.slug or '—'}\n")
        if s.subtitle:
            out.write(
                f"  {dim}subtitle{rst} {clip_text(s.subtitle, max_subtitle_len)}\n"
            )
        meta_parts = [p for p in (s.series_type, s.recurrence) if p.strip()]
        if meta_parts:
            out.write(f"  {dim}{' · '.join(meta_parts)}{rst}\n")

        st = (
            f"{accent}● active{rst}"
            if s.active and not s.closed
            else f"{dim}○ closed / inactive{rst}"
        )
        out.write(f"  {st}\n")

        vol = format_display_num(s.volume)
        v24 = format_vol_24h(s.volume_24h)
        liq = format_display_num(s.liquidity)
        out.write(
            f"  {dim}vol{rst} {vol}  {dim}24h{rst} {v24}  {dim}liq{rst} {liq}  "
            f"{dim}events in scan{rst} {s.event_count}\n"
        )
        out.write("\n")
