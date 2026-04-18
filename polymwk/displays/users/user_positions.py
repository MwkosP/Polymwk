"""Print a user's open :class:`~polymwk.models.Position` or closed :class:`~polymwk.models.UserClosedPosition` rows."""

from __future__ import annotations

import math
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TextIO, cast

from polymwk.exceptions import PolymwkError
from polymwk.models import Position, UserClosedPosition
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    format_display_num,
    strip_ansi,
    term_style,
    term_width,
)


def _pad_vis(s: str, width: int) -> str:
    return s + " " * max(0, width - len(strip_ansi(s)))


def _fmt_price(x: float) -> str:
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


def _fmt_closed_at(ts: datetime | None) -> str:
    if ts is None:
        return "—"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.strftime("%Y-%m-%d")


def _pnl_styles(stream: TextIO, x: float) -> tuple[str, str]:
    if not getattr(stream, "isatty", lambda: False)():
        return ("", "")
    if isinstance(x, float) and math.isnan(x):
        return ("", "")
    if x > 0:
        return ("\033[92m", "\033[0m")
    if x < 0:
        return ("\033[91m", "\033[0m")
    return ("", "")


def displayUserPositions(
    positions: Sequence[Position] | Sequence[UserClosedPosition],
    *,
    stream: TextIO | None = None,
    status: str = "active",
) -> None:
    """
    Pretty-print rows from :func:`~polymwk.users.positions.fetchUserPositions`.

    Use ``status='active'`` with :class:`~polymwk.models.Position` rows and
    ``status='closed'`` with :class:`~polymwk.models.UserClosedPosition` rows.
    """
    out = stream if stream is not None else sys.stdout
    if isinstance(positions, (str, bytes)) or not isinstance(positions, Sequence):
        raise PolymwkError(
            "displayUserPositions expects a sequence of Position or UserClosedPosition"
        )
    for p in positions:
        if status == "closed":
            if not isinstance(p, UserClosedPosition):
                raise PolymwkError(
                    "displayUserPositions(..., status='closed') expects "
                    "polymwk.models.UserClosedPosition rows"
                )
        else:
            if not isinstance(p, Position):
                raise PolymwkError(
                    "displayUserPositions(..., status='active') expects "
                    "polymwk.models.Position rows"
                )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner_w = min(88, max(48, term_w - 4))
    n = len(positions)

    line_title = f"{bold}User positions{rst}"
    line_sub = f"{accent}{status}{rst} {dim}·{rst} {dim}{n} row{'s' if n != 1 else ''}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    wallet = positions[0].wallet if positions else "—"
    out.write(f"  {dim}wallet:{rst} {accent}{clip_text(wallet, 66)}{rst}\n\n")

    if not positions:
        out.write(f"  {dim}(no positions){rst}\n\n")
        return

    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    title_w = max(16, min(40, term_w - 58))

    if status == "closed":
        hdr = (
            f"  {dim}{'#':>3}{rst}  "
            f"{dim}{_pad_vis('market', title_w)}{rst}  "
            f"{dim}{'out':<8}{rst}  "
            f"{dim}{'bought':>8}{rst}  "
            f"{dim}{'avg':>6}{rst}  "
            f"{dim}{'last':>6}{rst}  "
            f"{dim}{'rPnL':>9}{rst}  "
            f"{dim}{'closed':>10}{rst}\n"
        )
        out.write(hdr)
        emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
        closed_rows = cast(Sequence[UserClosedPosition], positions)
        for i, p in enumerate(closed_rows, start=1):
            title = clip_text(p.market_title, title_w)
            title_cell = _pad_vis(f"{accent}{title}{rst}", title_w)
            tb = format_display_num(p.total_bought)
            r0, r1 = _pnl_styles(out, p.realized_pnl)
            rp = f"{r0}{_fmt_pnl_dollar(p.realized_pnl)}{r1}"
            oc = clip_text(p.outcome, 8)
            ocell = f"{dim}{_pad_vis(oc, 8)}{rst}"
            out.write(
                f"  {dim}{i:>3}{rst}  "
                f"{title_cell}  "
                f"{ocell}  "
                f"{dim}{tb:>8}{rst}  "
                f"{dim}{_fmt_price(p.avg_price):>6}{rst}  "
                f"{dim}{_fmt_price(p.current_price):>6}{rst}  "
                f"{_pad_vis(rp, 9)}  "
                f"{dim}{_fmt_closed_at(p.closed_at):>10}{rst}\n"
            )
    else:
        hdr = (
            f"  {dim}{'#':>3}{rst}  "
            f"{dim}{_pad_vis('market', title_w)}{rst}  "
            f"{dim}{'out':<8}{rst}  "
            f"{dim}{'size':>8}{rst}  "
            f"{dim}{'avg':>6}{rst}  "
            f"{dim}{'now':>6}{rst}  "
            f"{dim}{'value':>8}{rst}  "
            f"{dim}{'uPnL':>9}{rst}  "
            f"{dim}{'rPnL':>9}{rst}\n"
        )
        out.write(hdr)
        emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
        open_rows = cast(Sequence[Position], positions)
        for i, p in enumerate(open_rows, start=1):
            title = clip_text(p.market_title, title_w)
            title_cell = _pad_vis(f"{accent}{title}{rst}", title_w)
            sz = format_display_num(p.size)
            val = format_display_num(p.current_value)
            u0, u1 = _pnl_styles(out, p.unrealised_pnl)
            r0, r1 = _pnl_styles(out, p.realised_pnl)
            up = f"{u0}{_fmt_pnl_dollar(p.unrealised_pnl)}{u1}"
            rp = f"{r0}{_fmt_pnl_dollar(p.realised_pnl)}{r1}"
            oc = clip_text(p.outcome, 8)
            ocell = f"{dim}{_pad_vis(oc, 8)}{rst}"
            out.write(
                f"  {dim}{i:>3}{rst}  "
                f"{title_cell}  "
                f"{ocell}  "
                f"{dim}{sz:>8}{rst}  "
                f"{dim}{_fmt_price(p.avg_price):>6}{rst}  "
                f"{dim}{_fmt_price(p.current_price):>6}{rst}  "
                f"{dim}{val:>8}{rst}  "
                f"{_pad_vis(up, 9)}  "
                f"{_pad_vis(rp, 9)}\n"
            )

    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    out.write("\n")
