"""Print polymwk events for quick inspection."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import Event
from polymwk.displays.utils import (
    center_line,
    clip_text,
    content_width,
    description_char_cap,
    description_gray,
    description_worth_showing,
    emit_centered_yes_no,
    emit_horizontal_rule,
    emit_market_list_item,
    emit_menu_header,
    emit_short_centered_separator,
    format_display_num,
    format_vol_24h,
    market_count_display,
    section_label_white,
    term_style,
    term_width,
    wrap_line,
)


def displayEvents(
    events: Event | Sequence[Event],
    *,
    tags: str | Sequence[str] | None = None,
    stream: TextIO | None = None,
    max_description_len: int = 10_000,
    max_description_lines: int = 2,
    show_description: bool = True,
    show_vol: bool = True,
    show_yesno: bool = True,
    show_markets: bool = False,
) -> None:
    """
    Pretty-print one or more :class:`~polymwk.models.Event` to ``stream`` (default stdout).

    ``tags`` is shown in the centered header (e.g. ``\"bitcoin\"`` or ``[\"btc\", \"eth\"]``).
    When ``show_description`` is True, the description is shown in muted gray, clipped
    to fit at most ``max_description_lines`` (default 2) of wrapped text, with ``...``
    when truncated. ``max_description_len`` is an extra upper bound if set lower.

    When ``show_yesno`` is True, implied Yes/No percentages from the **primary**
    market (first in the list, or :attr:`~polymwk.models.Event.primary_yes_price`
    when markets were stripped by ``fetchEvents``) are printed centered, directly
    under the ``ends`` line (or under the stats line if there is no end date).

    When ``show_markets`` is True and the event includes ``markets``, each outcome
    is listed as ``- question`` with Yes/No percentages and (if ``show_vol``)
    total and 24h volume on the following indented line.
    """
    out = stream if stream is not None else sys.stdout
    bold, dim, accent, rst = term_style(out)
    desc_gray = description_gray(out)
    section_white = section_label_white(out)
    term_w = term_width(out)
    inner_w = content_width(stream)
    base_indent = "  "
    cont_indent = "  "
    desc_lines = max(1, min(max_description_lines, 4))

    rows: list[Event] = [events] if isinstance(events, Event) else list(events)
    if not rows:
        emit_menu_header(
            out, tags=tags, bold=bold, dim=dim, accent=accent, rst=rst, term_w=term_w
        )
        center_line(out, f"{dim}(no events){rst}", term_w)
        out.write("\n")
        return

    emit_menu_header(
        out, tags=tags, bold=bold, dim=dim, accent=accent, rst=rst, term_w=term_w
    )

    for i, ev in enumerate(rows, start=1):
        if not isinstance(ev, Event):
            raise PolymwkError("displayEvents expects polymwk.models.Event instances")

        mc = market_count_display(ev)
        status_lbl = f"{accent}● active{rst}" if ev.active else f"{dim}○ inactive{rst}"

        emit_horizontal_rule(
            out,
            inner_w,
            dim=dim,
            rst=rst,
            label=f"{i} / {len(rows)}",
        )

        out.write(f"{base_indent}{section_white}Event{rst}\n")
        out.write(f"{base_indent}{accent}{ev.slug}{rst}\n")
        for line in wrap_line(
            ev.title,
            inner_w,
            f"{base_indent}{bold}",
            f"{cont_indent}  ",
        ):
            out.write(f"{line}{rst}\n")

        if show_description:
            if description_worth_showing(ev.description, ev.title):
                first_d = f"{base_indent}{desc_gray}"
                cont_d = f"{cont_indent}  {desc_gray}"
                cap = min(
                    description_char_cap(inner_w, first_d, cont_d, desc_lines),
                    max_description_len,
                )
                desc = clip_text(ev.description, cap)
                if desc:
                    wrapped = wrap_line(desc, inner_w, first_d, cont_d)
                    while len(wrapped) > desc_lines and cap > 24:
                        cap = max(24, cap - max(16, cap // 6))
                        desc = clip_text(ev.description, cap)
                        wrapped = wrap_line(desc, inner_w, first_d, cont_d)
                    for line in wrapped[:desc_lines]:
                        out.write(f"{line}{rst}\n")

        meta_parts: list[str] = [f"{mc} market{'s' if mc != 1 else ''}", status_lbl]
        if show_vol:
            v24 = format_vol_24h(ev.volume_24h)
            meta_parts.insert(
                0,
                f"vol {dim}{format_display_num(ev.volume)}{rst}  ·  24h {dim}{v24}{rst}",
            )
        out.write(base_indent + f" {dim}·{rst} ".join(meta_parts) + "\n")

        if ev.end_date is not None:
            out.write(
                f"{base_indent}{dim}ends {ev.end_date.isoformat()}{rst}\n"
            )

        if show_yesno:
            yes_p: float | None = None
            no_p: float | None = None
            if ev.markets:
                yes_p = ev.markets[0].yes_price
                no_p = ev.markets[0].no_price
            elif ev.primary_yes_price is not None and ev.primary_no_price is not None:
                yes_p = ev.primary_yes_price
                no_p = ev.primary_no_price
            if yes_p is not None and no_p is not None:
                emit_centered_yes_no(
                    out,
                    term_w=term_w,
                    yes_price=yes_p,
                    no_price=no_p,
                    dim=dim,
                    accent=accent,
                    rst=rst,
                )

        if show_markets and ev.markets:
            out.write("\n")
            emit_short_centered_separator(out, inner_w=inner_w, dim=dim, rst=rst)
            out.write(f"{base_indent}{section_white}Markets{rst}\n")
            for mkt in ev.markets:
                emit_market_list_item(
                    out,
                    mkt,
                    inner_w=inner_w,
                    base_indent=base_indent,
                    show_vol=show_vol,
                    dim=dim,
                    accent=accent,
                    desc_gray=desc_gray,
                    rst=rst,
                )

        out.write("\n")
