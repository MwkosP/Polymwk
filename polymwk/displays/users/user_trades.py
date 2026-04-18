"""Print a user's :class:`~polymwk.models.Trade` rows (e.g. from ``fetchUserTrades``)."""

from __future__ import annotations

import math
import sys
from collections.abc import Sequence
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import Trade
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    format_display_num,
    format_relative_ago,
    strip_ansi,
    term_style,
    term_width,
)


def _pad_vis(s: str, width: int) -> str:
    return s + " " * max(0, width - len(strip_ansi(s)))


def _fmt_price_cents(p: float) -> str:
    if isinstance(p, float) and math.isnan(p):
        return "—"
    if 0.0 <= p <= 1.0:
        return f"{p * 100:.1f}¢"
    return f"{p:.2f}"


def displayUserTrades(
    trades: Sequence[Trade],
    *,
    stream: TextIO | None = None,
) -> None:
    """Pretty-print :class:`~polymwk.models.Trade` rows (newest-first if the API sorted that way)."""
    out = stream if stream is not None else sys.stdout
    if isinstance(trades, (str, bytes)) or not isinstance(trades, Sequence):
        raise PolymwkError("displayUserTrades expects a sequence of polymwk.models.Trade")
    for t in trades:
        if not isinstance(t, Trade):
            raise PolymwkError("displayUserTrades expects a sequence of polymwk.models.Trade")

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner_w = min(88, max(48, term_w - 4))
    n = len(trades)

    line_title = f"{bold}User trades{rst}"
    line_sub = f"{dim}{n} fill{'s' if n != 1 else ''}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    wallet = trades[0].wallet if trades else "—"
    out.write(f"  {dim}wallet:{rst} {accent}{clip_text(wallet, 66)}{rst}\n\n")

    if not trades:
        out.write(f"  {dim}(no trades){rst}\n\n")
        return

    title_w = max(14, min(30, term_w - 58))
    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    hdr = (
        f"  {dim}{'#':>3}{rst}  "
        f"{dim}{'when':<10}{rst}  "
        f"{dim}{'side':<5}{rst}  "
        f"{dim}{_pad_vis('market', title_w)}{rst}  "
        f"{dim}{'out':<7}{rst}  "
        f"{dim}{'px':>6}{rst}  "
        f"{dim}{'size':>8}{rst}  "
        f"{dim}{'$':>8}{rst}  "
        f"{dim}{'tx':<10}{rst}\n"
    )
    out.write(hdr)
    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)

    for i, t in enumerate(trades, start=1):
        when = clip_text(format_relative_ago(t.timestamp), 10)
        sd = clip_text(t.side, 5)
        side_cell = f"{dim}{_pad_vis(sd, 5)}{rst}"
        mkt = clip_text(t.market_title or t.market_slug or "—", title_w)
        title_cell = _pad_vis(f"{accent}{mkt}{rst}", title_w)
        oc = clip_text(t.outcome, 7)
        ocell = f"{dim}{_pad_vis(oc, 7)}{rst}"
        px = _fmt_price_cents(t.price)
        sz = format_display_num(t.size)
        usd = format_display_num(t.value_usd)
        tx = clip_text(t.tx_hash, 10) if t.tx_hash else "—"
        out.write(
            f"  {dim}{i:>3}{rst}  "
            f"{dim}{_pad_vis(when, 10)}{rst}  "
            f"{side_cell}  "
            f"{title_cell}  "
            f"{ocell}  "
            f"{dim}{px:>6}{rst}  "
            f"{dim}{sz:>8}{rst}  "
            f"{dim}{usd:>8}{rst}  "
            f"{dim}{tx:<10}{rst}\n"
        )

    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    out.write("\n")
