"""Print ``EventCommentsSnapshot`` (site-style thread)."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import EventCommentsSnapshot
from polymwk.displays.utils import (
    clip_text,
    content_width,
    emit_boxed_header,
    format_relative_ago,
    section_label_white,
    term_style,
    term_width,
    wrap_line,
)


def displayEventComments(
    snapshot: EventCommentsSnapshot,
    *,
    stream: TextIO | None = None,
    max_body_lines: int = 12,
) -> None:
    """
    One block per comment: author, wrapped body, relative time (and reply marker).
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, EventCommentsSnapshot):
        raise PolymwkError(
            "displayEventComments expects polymwk.models.EventCommentsSnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    section_white = section_label_white(out)
    term_w = term_width(out)
    inner_w = content_width(stream)

    sub = snapshot.event_slug or str(snapshot.event_id)
    line_title = f"{bold}Comments{rst}"
    line_sub = f"{accent}{sub}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )
    title = clip_text(snapshot.event_title, 70) if snapshot.event_title else "—"
    out.write(
        f"  {dim}Event:{rst} {section_white}{title}{rst}\n"
        f"  {dim}id:{rst} {dim}{snapshot.event_id}{rst}  "
        f"{dim}slug:{rst} {accent}{snapshot.event_slug or '—'}{rst}\n\n"
    )

    rows = snapshot.comments
    if not rows:
        out.write(f"  {dim}(no comments){rst}\n\n")
        return

    for row in rows:
        is_reply = bool(row.parent_comment_id)
        ind = "    " if is_reply else "  "
        tag = f"{dim}↳{rst} " if is_reply else ""
        out.write(f"{ind}{tag}{accent}{row.display_name}{rst}\n")
        body = row.body.strip() if row.body else "(empty)"
        first = f"{ind}  {dim}"
        cont = f"{ind}  {dim}"
        lines = wrap_line(body, inner_w, first, cont)
        if len(lines) > max_body_lines:
            lines = lines[:max_body_lines]
            lines.append(f"{ind}  {dim}…")
        for ln in lines:
            out.write(f"{ln}{rst}\n")
        meta = format_relative_ago(row.created_at)
        out.write(f"{ind}  {dim}{meta}{rst}")
        if row.reaction_count > 0:
            out.write(f"{dim} · {row.reaction_count} reactions{rst}")
        out.write("\n\n")
