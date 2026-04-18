"""Print ``MarketTopHoldersSnapshot`` (Data API /holders)."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import MarketTopHoldersSnapshot
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    format_display_num,
    section_label_white,
    term_style,
    term_width,
)


def displayMarketTopHolders(
    snapshot: MarketTopHoldersSnapshot,
    *,
    stream: TextIO | None = None,
    max_per_group: int = 15,
) -> None:
    """
    Pretty-print :class:`~polymwk.models.MarketTopHoldersSnapshot` (Yes/No or multi-outcome groups).

    Shows up to ``max_per_group`` rows per outcome token, with rank, truncated wallet,
    display name, and size.
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, MarketTopHoldersSnapshot):
        raise PolymwkError(
            "displayMarketTopHolders expects polymwk.models.MarketTopHoldersSnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    section_white = section_label_white(out)
    term_w = term_width(out)
    inner_w = min(88, max(48, term_w - 4))

    line_title = f"{bold}Top holders{rst}"
    line_sub = f"{accent}{snapshot.market_slug}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )
    ev = snapshot.event_slug.strip() or "—"
    out.write(
        f"  {dim}Market:{rst} {accent}{snapshot.market_slug}{rst}\n"
        f"  {dim}Event:{rst} {accent}{clip_text(ev, 66)}{rst}\n"
        f"  {dim}condition:{rst} {dim}{clip_text(snapshot.condition_id, 66)}{rst}\n\n"
    )

    if not snapshot.groups:
        out.write(f"  {dim}(no holder groups){rst}\n\n")
        return

    for gi, group in enumerate(snapshot.groups):
        if gi:
            out.write("\n")
        emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
        out.write(
            f"  {section_white}{group.outcome_label}{rst} {dim}· token {clip_text(group.token_id, 24)}{rst}\n"
        )
        emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
        out.write(
            f"  {dim}{'#':>3}{rst}  {dim}{'wallet':<18}{rst}  "
            f"{dim}{'name':<20}{rst}  {dim}{'size':>12}{rst}\n"
        )
        rows = group.holders[: max(0, max_per_group)]
        for i, h in enumerate(rows, start=1):
            wvis = clip_text(h.wallet, 16)
            nick = clip_text(h.pseudonym or h.name or "—", 18)
            out.write(
                f"  {dim}{i:>3}{rst}  {accent}{wvis:<18}{rst}  "
                f"{dim}{nick:<20}{rst}  {format_display_num(h.size):>12}\n"
            )
        if len(group.holders) > max_per_group:
            more = len(group.holders) - max_per_group
            out.write(f"  {dim}… {more} more{rst}\n")

    out.write("\n")

