"""Terminal chart for ``MarketPricesSnapshot`` (CLOB history) via plotille (braille)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from typing import TextIO

import plotille

from polymwk.exceptions import PolymwkError
from polymwk.models import MarketPricesSnapshot
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    term_style,
    term_width,
)


def _fmt_ts(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    else:
        ts = ts.astimezone(UTC)
    return ts.strftime("%m-%d %H:%M")


def _ensure_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


def _y_limits_pct(y_pct: list[float]) -> tuple[float, float]:
    lo, hi = min(y_pct), max(y_pct)
    if hi - lo < 1e-9:
        return lo - 0.5, hi + 0.5
    pad = max((hi - lo) * 0.06, 0.12)
    return lo - pad, hi + pad


def displayMarketPrices(
    snapshot: MarketPricesSnapshot,
    *,
    stream: TextIO | None = None,
    chart_width: int | None = None,
    chart_height: int = 16,
    area_fill: bool = True,
) -> None:
    """
    Boxed header, stats, then a **plotille** braille line chart (time × implied %).

    ``area_fill`` is retained for API compatibility; plotille draws an interpolated
    line only (no shaded area).
    """
    _ = area_fill
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, MarketPricesSnapshot):
        raise PolymwkError(
            "displayMarketPrices expects polymwk.models.MarketPricesSnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    # plotille adds Y-axis ticks (~18–22 cols) + frame; keep total within terminal
    axis_slack = 22
    max_inner = max(28, term_w - 4 - axis_slack)
    tw = chart_width if chart_width is not None else max(28, min(max_inner, 100))
    th = max(8, min(chart_height, 40))

    line_title = f"{bold}Prices{rst}"
    line_sub = f"{accent}{snapshot.market_slug}{rst} {dim}·{rst} {accent}{snapshot.outcome_label}{rst}"
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
        f"  {dim}token:{rst} {dim}{clip_text(snapshot.token_id, 62)}{rst}\n"
        f"  {dim}interval:{rst} {snapshot.interval}  {dim}fidelity:{rst} {snapshot.fidelity} min\n\n"
    )

    pts = snapshot.points
    if not pts:
        out.write(f"  {dim}(no price points){rst}\n\n")
        return

    X = [_ensure_utc(p.timestamp) for p in pts]
    y_pct = [float(p.price) * 100.0 for p in pts]
    t0, t1 = pts[0].timestamp, pts[-1].timestamp
    lo, hi = min(y_pct), max(y_pct)
    last = y_pct[-1]
    out.write(
        f"  {dim}samples:{rst} {len(pts)}  "
        f"{dim}range:{rst} {_fmt_ts(t0)} {dim}→{rst} {_fmt_ts(t1)}\n"
        f"  {dim}min:{rst} {lo:.1f}%  {dim}max:{rst} {hi:.1f}%  "
        f"{dim}last:{rst} {accent}{last:.1f}%{rst}\n\n"
    )

    y_min, y_max = _y_limits_pct(y_pct)
    tty = getattr(out, "isatty", lambda: False)()
    lc: str | None = "cyan" if tty else None

    block = plotille.plot(
        X,
        y_pct,
        width=tw,
        height=th,
        X_label="UTC",
        Y_label="%",
        interp="linear",
        y_min=y_min,
        y_max=y_max,
        lc=lc,
        color_mode="names",
        origin=True,
    )
    out.write(f"  {dim}chart (plotille {tw}×{th}){rst}\n")
    for line in block.splitlines():
        out.write(f"  {line}\n")
    out.write("\n")
