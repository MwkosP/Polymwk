"""Print a user's :class:`~polymwk.models.Activity` rows (e.g. from ``fetchUserActivity``)."""

from __future__ import annotations

import math
import sys
from collections.abc import Sequence
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import Activity
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


def displayUserActivity(
    activities: Sequence[Activity],
    *,
    stream: TextIO | None = None,
) -> None:
    """
    Pretty-print :class:`~polymwk.models.Activity` rows (newest-first if the API
    sorted that way).
    """
    out = stream if stream is not None else sys.stdout
    if isinstance(activities, (str, bytes)) or not isinstance(activities, Sequence):
        raise PolymwkError(
            "displayUserActivity expects a sequence of polymwk.models.Activity"
        )
    for a in activities:
        if not isinstance(a, Activity):
            raise PolymwkError(
                "displayUserActivity expects a sequence of polymwk.models.Activity"
            )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner_w = min(88, max(48, term_w - 4))
    n = len(activities)

    line_title = f"{bold}User activity{rst}"
    line_sub = f"{dim}{n} event{'s' if n != 1 else ''}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    wallet = activities[0].wallet if activities else "—"
    out.write(f"  {dim}wallet:{rst} {accent}{clip_text(wallet, 66)}{rst}\n\n")

    if not activities:
        out.write(f"  {dim}(no activity){rst}\n\n")
        return

    title_w = max(14, min(32, term_w - 62))

    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    hdr = (
        f"  {dim}{'#':>3}{rst}  "
        f"{dim}{'when':<10}{rst}  "
        f"{dim}{'type':<12}{rst}  "
        f"{dim}{_pad_vis('market', title_w)}{rst}  "
        f"{dim}{'side':<5}{rst}  "
        f"{dim}{'px':>6}{rst}  "
        f"{dim}{'$':>8}{rst}\n"
    )
    out.write(hdr)
    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)

    for i, a in enumerate(activities, start=1):
        when = "—"
        if a.timestamp is not None:
            when = format_relative_ago(a.timestamp)
        when = clip_text(when, 10)
        typ = clip_text(a.type, 12)
        mkt = clip_text(a.market_title or a.market_slug or "—", title_w)
        title_cell = _pad_vis(f"{accent}{mkt}{rst}", title_w)
        side = clip_text((a.side or "—"), 5)
        side_cell = f"{dim}{_pad_vis(side, 5)}{rst}"
        px = _fmt_price_cents(a.price)
        usd = format_display_num(a.usdc_size)
        out.write(
            f"  {dim}{i:>3}{rst}  "
            f"{dim}{_pad_vis(when, 10)}{rst}  "
            f"{dim}{_pad_vis(typ, 12)}{rst}  "
            f"{title_cell}  "
            f"{side_cell}  "
            f"{dim}{px:>6}{rst}  "
            f"{dim}{usd:>8}{rst}\n"
        )

    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    out.write("\n")
