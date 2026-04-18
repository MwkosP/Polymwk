"""Print :class:`~polymwk.models.TagsConfigSnapshot` (config keyword tree)."""

from __future__ import annotations

import sys
import textwrap
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import TagsConfigSnapshot
from polymwk.displays.utils import emit_boxed_header, emit_horizontal_rule, term_style, term_width


def displayTags(
    snapshot: TagsConfigSnapshot,
    *,
    stream: TextIO | None = None,
    wrap_width: int | None = None,
) -> None:
    """
    Pretty-print configured tag categories and each subgroup's search keywords.

    ``wrap_width`` defaults to a value derived from terminal width (capped); set it
    explicitly for tests or narrow logs.
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, TagsConfigSnapshot):
        raise PolymwkError("displayTags expects polymwk.models.TagsConfigSnapshot")

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner = min(100, max(52, term_w - 4))
    kw_w = wrap_width if wrap_width is not None else max(40, inner - 6)

    emit_boxed_header(
        out,
        lines=(
            f"{bold}Tag keywords{rst}",
            f"{dim}{snapshot.source}{rst}",
        ),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )
    out.write(
        f"  {dim}Each subgroup lists strings used for coarse text / query matching.{rst}\n"
        f"  {dim}Edit lists in polymwk/configs/tags.py, then call fetchTags() again.{rst}\n\n"
    )

    if not snapshot.categories:
        out.write(f"  {dim}(no categories){rst}\n\n")
        return

    for ci, cat in enumerate(snapshot.categories):
        if ci:
            out.write("\n")
        emit_horizontal_rule(out, inner, dim=dim, rst=rst)
        out.write(f"  {accent}{cat.slug}{rst} {dim}({len(cat.entries)} subgroups){rst}\n")
        emit_horizontal_rule(out, inner, dim=dim, rst=rst)

        for ent in cat.entries:
            n = len(ent.keywords)
            out.write(f"\n  {bold}{ent.slug}{rst} {dim}·{rst} {dim}{n} keyword{'s' if n != 1 else ''}{rst}\n")
            if not ent.keywords:
                out.write(f"    {dim}(empty){rst}\n")
                continue
            blob = ", ".join(ent.keywords)
            wrapped = textwrap.fill(
                blob,
                width=kw_w,
                initial_indent="    ",
                subsequent_indent="    ",
                break_long_words=False,
                break_on_hyphens=False,
            )
            out.write(wrapped + "\n")

    out.write("\n")
