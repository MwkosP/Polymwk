"""Print ``MarketLastActivitySnapshot`` (site-style trade feed)."""

from __future__ import annotations

import math
import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import MarketLastActivitySnapshot
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    format_relative_ago,
    term_style,
    term_width,
)


def _fmt_trade_size(n: float) -> str:
    if isinstance(n, float) and math.isnan(n):
        return "—"
    if abs(n - round(n)) < 1e-6:
        return f"{int(round(n)):,}"
    s = f"{n:,.2f}".rstrip("0").rstrip(".")
    return s


def _fmt_trade_price_cents(p: float) -> str:
    if isinstance(p, float) and math.isnan(p):
        return "—"
    c = p * 100.0
    if c < 10.0 and abs(c * 10 - round(c * 10)) > 0.05:
        return f"{c:.2f}¢"
    return f"{c:.1f}¢"


def _fmt_trade_usd_parens(x: float) -> str:
    if isinstance(x, float) and math.isnan(x):
        return "(—)"
    if abs(x - round(x)) < 0.005:
        return f"(${int(round(x)):,})"
    return f"(${x:,.2f})"


def displayMarketLastActivity(
    snapshot: MarketLastActivitySnapshot,
    *,
    stream: TextIO | None = None,
) -> None:
    """
    One block per trade: ``name bought 298 Yes at 91.0¢ ($271)`` then relative time.
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, MarketLastActivitySnapshot):
        raise PolymwkError(
            "displayMarketLastActivity expects polymwk.models.MarketLastActivitySnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)

    line_title = f"{bold}Activity{rst}"
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

    rows = snapshot.activities
    if not rows:
        out.write(f"  {dim}(no trades){rst}\n\n")
        return

    for row in rows:
        verb = "bought" if row.side == "BUY" else "sold"
        sz = _fmt_trade_size(row.size)
        oc = row.outcome.strip() or "—"
        pc = _fmt_trade_price_cents(row.price)
        usd = _fmt_trade_usd_parens(row.value_usd)
        rel = format_relative_ago(row.timestamp)
        out.write(
            f"  {accent}{row.display_name}{rst} {dim}{verb}{rst} "
            f"{dim}{sz}{rst} {accent}{oc}{rst} {dim}at {rst}{dim}{pc}{rst} {dim}{usd}{rst}\n"
            f"  {dim}{rel}{rst}\n\n"
        )
