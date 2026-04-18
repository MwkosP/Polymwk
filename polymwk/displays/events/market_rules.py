"""Boxed terminal view for ``MarketRulesSnapshot`` (Gamma rules / resolution)."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import MarketRulesSnapshot
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    term_style,
    term_width,
    wrap_line,
)


def displayMarketRules(
    snapshot: MarketRulesSnapshot,
    *,
    stream: TextIO | None = None,
) -> None:
    """
    Boxed **Rules** header, then resolution source, market question, rules body,
    and optional event-level description (same layout spirit as ``displayMarketPrices``).
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, MarketRulesSnapshot):
        raise PolymwkError(
            "displayMarketRules expects polymwk.models.MarketRulesSnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner_w = max(40, term_w - 2)
    base = "  "

    line_title = f"{bold}Rules{rst}"
    line_sub = f"{accent}{snapshot.market_slug}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
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

    if snapshot.uma_resolution_status:
        out.write(
            f"  {dim}UMA status:{rst} {accent}{snapshot.uma_resolution_status}{rst}\n\n"
        )

    if snapshot.resolution_source:
        emit_horizontal_rule(
            out,
            min(inner_w, 72),
            dim=dim,
            rst=rst,
            label="Resolution source",
        )
        out.write("\n")
        src = snapshot.resolution_source
        for line in wrap_line(
            src,
            inner_w,
            f"{base}{accent}",
            f"{base}{accent}",
        ):
            out.write(f"{line}{rst}\n")
        out.write("\n")

    emit_horizontal_rule(
        out,
        min(inner_w, 72),
        dim=dim,
        rst=rst,
        label="Rules",
    )
    out.write("\n")
    body = snapshot.rules_body.strip()
    if body:
        bi = f"{base}{dim}"
        bc = f"{base}{dim}"
        for para in body.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            for line in para.split("\n"):
                line = line.strip()
                if not line:
                    out.write("\n")
                    continue
                for wl in wrap_line(line, inner_w, bi, bc):
                    out.write(f"{wl}{rst}\n")
            out.write("\n")
    else:
        out.write(f"  {dim}(no market rules text in Gamma){rst}\n\n")

    ed = snapshot.event_description.strip()
    if ed:
        emit_horizontal_rule(
            out,
            min(inner_w, 72),
            dim=dim,
            rst=rst,
            label="Event description",
        )
        out.write("\n")
        bi = f"{base}{dim}"
        bc = f"{base}{dim}"
        for para in ed.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            for line in para.split("\n"):
                line = line.strip()
                if not line:
                    out.write("\n")
                    continue
                for wl in wrap_line(line, inner_w, bi, bc):
                    out.write(f"{wl}{rst}\n")
            out.write("\n")
