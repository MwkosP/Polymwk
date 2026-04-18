"""Terminal view for ``MarketResolutionSnapshot`` (Gamma resolution / UMA fields)."""

from __future__ import annotations

import sys
from datetime import UTC
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import MarketResolutionSnapshot
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    term_style,
    term_width,
    wrap_line,
)


def _fmt_dt(dt) -> str:
    if dt is None:
        return "—"
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _tri(v: bool | None) -> str:
    if v is None:
        return "—"
    return "yes" if v else "no"


def displayMarketResolution(
    snapshot: MarketResolutionSnapshot,
    *,
    stream: TextIO | None = None,
) -> None:
    """
    Boxed **Resolution** header, then Gamma fields: ids, closed state, UMA status/dates,
    bond/reward, resolution source (wrapped).
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, MarketResolutionSnapshot):
        raise PolymwkError(
            "displayMarketResolution expects polymwk.models.MarketResolutionSnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner_w = max(40, term_w - 2)
    base = "  "

    emit_boxed_header(
        out,
        lines=(f"{bold}Resolution{rst}", f"{accent}{snapshot.market_slug}{rst}"),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    ev = snapshot.event_slug.strip() or "—"
    et = snapshot.event_title.strip()
    ev_line = f"{accent}{clip_text(ev, 66)}{rst}"
    if et:
        ev_line += f" {dim}·{rst} {dim}{clip_text(et, 48)}{rst}"
    out.write(
        f"  {dim}Market:{rst} {accent}{snapshot.market_slug}{rst}\n"
        f"  {dim}Event:{rst} {ev_line}\n"
    )
    q = snapshot.market_question.strip()
    if q:
        out.write(f"  {dim}Question:{rst} {accent}{clip_text(q, 72)}{rst}\n")
    out.write("\n")

    out.write(
        f"  {dim}conditionId:{rst} {dim}{clip_text(snapshot.condition_id, 68) or '—'}{rst}\n"
        f"  {dim}questionID:{rst} {dim}{clip_text(snapshot.question_id, 68) or '—'}{rst}\n"
        f"  {dim}closed:{rst} {accent}{_tri(snapshot.closed)}{rst}  "
        f"{dim}archived:{rst} {accent}{_tri(snapshot.archived)}{rst}  "
        f"{dim}active:{rst} {accent}{_tri(snapshot.active)}{rst}\n"
    )
    ct = snapshot.closed_time.strip()
    if ct:
        out.write(f"  {dim}closedTime:{rst} {dim}{clip_text(ct, 72)}{rst}\n")
    rb = snapshot.resolved_by.strip()
    if rb:
        out.write(f"  {dim}resolvedBy:{rst} {dim}{clip_text(rb, 72)}{rst}\n")
    out.write("\n")

    emit_horizontal_rule(out, min(inner_w, 72), dim=dim, rst=rst, label="UMA (Gamma)")
    out.write("\n")
    uma = snapshot.uma_resolution_status
    out.write(
        f"  {dim}umaResolutionStatus:{rst} "
        f"{accent if uma else dim}{uma or '—'}{rst}\n"
        f"  {dim}umaEndDate:{rst} {dim}{_fmt_dt(snapshot.uma_end_date)}{rst}\n"
        f"  {dim}umaEndDateIso:{rst} {dim}{_fmt_dt(snapshot.uma_end_date_iso)}{rst}\n"
        f"  {dim}umaBond:{rst} {dim}{snapshot.uma_bond or '—'}{rst}\n"
        f"  {dim}umaReward:{rst} {dim}{snapshot.uma_reward or '—'}{rst}\n"
        "\n",
    )

    src = snapshot.resolution_source.strip()
    if src:
        emit_horizontal_rule(
            out,
            min(inner_w, 72),
            dim=dim,
            rst=rst,
            label="Resolution source",
        )
        out.write("\n")
        for line in wrap_line(
            src,
            inner_w,
            f"{base}{accent}",
            f"{base}{accent}",
        ):
            out.write(f"{line}{rst}\n")
        out.write("\n")
