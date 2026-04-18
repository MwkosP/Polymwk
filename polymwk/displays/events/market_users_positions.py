"""Print ``MarketUsersPositionsSnapshot`` (site-style PnL lists per outcome)."""

from __future__ import annotations

import math
import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import MarketUsersPositionsSnapshot
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    format_display_num,
    section_label_white,
    strip_ansi,
    term_style,
    term_width,
)


def _fmt_prob_price(x: float) -> str:
    if isinstance(x, float) and math.isnan(x):
        return "—"
    if 0.0 <= x <= 1.0:
        return f"{x * 100:.1f}¢"
    return f"{x:.2f}"


def _fmt_pnl_dollar(x: float) -> str:
    if isinstance(x, float) and math.isnan(x):
        return "—"
    s = format_display_num(abs(x))
    if x > 0:
        return f"+${s}"
    if x < 0:
        return f"-${s}"
    return "$0"


def _pnl_styles(stream: TextIO, x: float) -> tuple[str, str]:
    if not getattr(stream, "isatty", lambda: False)():
        return ("", "")
    if isinstance(x, float) and math.isnan(x):
        return ("", "")
    if x > 0:
        return ("\033[92m", "\033[0m")
    if x < 0:
        return ("\033[91m", "\033[0m")
    return ("\033[2m", "\033[0m")


def _pad_vis(s: str, width: int) -> str:
    return s + (" " * max(0, width - len(strip_ansi(s))))


def displayMarketUsersPositions(
    snapshot: MarketUsersPositionsSnapshot,
    *,
    stream: TextIO | None = None,
    max_per_group: int = 200,
) -> None:
    """
    Pretty-print :class:`~polymwk.models.MarketUsersPositionsSnapshot` like the site:
    for each outcome, rows of **display name**, **avg** (¢), **PnL** ($, colored).
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, MarketUsersPositionsSnapshot):
        raise PolymwkError(
            "displayMarketUsersPositions expects polymwk.models.MarketUsersPositionsSnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    section_white = section_label_white(out)
    term_w = term_width(out)
    inner_w = min(88, max(48, term_w - 4))

    line_title = f"{bold}Positions{rst}"
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
        out.write(f"  {dim}(no position groups){rst}\n\n")
        return

    for gi, group in enumerate(snapshot.groups):
        if gi:
            out.write("\n")
        emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
        out.write(
            f"  {section_white}{group.outcome_label}{rst}  "
            f"{dim}· token {clip_text(group.token_id, 22)}{rst}\n"
        )
        emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
        out.write(
            f"  {dim}{'':30}{rst}  {dim}{'avg':>8}{rst}  {dim}{'PnL':>12}{rst}\n"
        )
        rows = group.positions[: max(0, max_per_group)]
        for p in rows:
            nm = clip_text(p.display_name, 30)
            av = _fmt_prob_price(p.avg_price)
            raw_pnl = _fmt_pnl_dollar(p.total_pnl)
            ps, pe = _pnl_styles(out, p.total_pnl)
            pnl = _pad_vis(f"{ps}{raw_pnl}{pe}" if ps else raw_pnl, 12)
            out.write(
                f"  {accent}{nm:<30}{rst}  {dim}{av:>8}{rst}  {pnl}\n"
            )
        if len(group.positions) > max_per_group:
            more = len(group.positions) - max_per_group
            out.write(f"  {dim}… {more} more{rst}\n")

    out.write("\n")
