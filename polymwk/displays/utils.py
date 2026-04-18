"""Terminal layout and formatting helpers for the displays package."""

from __future__ import annotations

import re
import shutil
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TextIO

from polymwk.models import Event, Market


def clip_text(text: str, max_len: int) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return "." * max_len
    return text[: max_len - 3] + "..."


def format_display_num(n: float) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 10_000:
        return f"{n / 1_000:.2f}k"
    if n >= 1_000:
        return f"{n:,.0f}"
    return f"{n:.2f}".rstrip("0").rstrip(".")


def format_relative_ago(ts: datetime, *, now: datetime | None = None) -> str:
    """Compact relative time: ``28s ago``, ``5m ago``, ``2h ago``, then date."""
    if now is None:
        now = datetime.now(UTC)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    else:
        ts = ts.astimezone(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    else:
        now = now.astimezone(UTC)
    sec = int((now - ts).total_seconds())
    if sec < 5:
        return "just now"
    if sec < 60:
        return f"{sec}s ago"
    minutes = sec // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h ago"
    days = hours // 24
    if days < 14:
        return f"{days}d ago"
    return ts.strftime("%Y-%m-%d")


def format_vol_24h(value: float | None) -> str:
    """Unknown 24h volume → em dash; real zero stays ``0``."""
    if value is None:
        return "—"
    return format_display_num(value)


def description_worth_showing(description: str, title: str) -> bool:
    """
    Skip junk/placeholder text Polymarket sometimes stores in ``description``
    (e.g. ``qqqqqq``, ``asd``) while keeping real copy.
    """
    d = description.replace("\n", " ").strip()
    if len(d) < 4:
        return False
    if d.casefold() == title.replace("\n", " ").strip().casefold():
        return False
    compact = d.replace(" ", "")
    if compact and len(set(compact)) == 1:
        return False
    return True


def market_count_display(ev: Event) -> int:
    return len(ev.markets) if ev.markets else ev.market_count


def strip_ansi(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", s)


def term_style(stream: TextIO) -> tuple[str, str, str, str]:
    if getattr(stream, "isatty", lambda: False)():
        return ("\033[1m", "\033[2m", "\033[36m", "\033[0m")
    return ("", "", "", "")


def description_gray(stream: TextIO) -> str:
    """Muted gray body text (separate from cyan slug / bold title)."""
    if getattr(stream, "isatty", lambda: False)():
        return "\033[2;37m"
    return ""


def section_label_white(stream: TextIO) -> str:
    """Bright white for ``Event`` / ``Markets`` section labels (TTY only)."""
    if getattr(stream, "isatty", lambda: False)():
        return "\033[1;97m"
    return ""


def exchange_depth_colors(stream: TextIO) -> tuple[str, str, str, str, str]:
    """
    Exchange-style depth ladder (TTY): bid / ask text colors + bar colors + reset.

    Returns ``(bid, ask, bar_bid, bar_ask, rst)``.
    """
    if getattr(stream, "isatty", lambda: False)():
        return (
            "\033[1;92m",  # bright green price/size
            "\033[1;91m",  # bright red
            "\033[32m",  # green bar
            "\033[31m",  # red bar
            "\033[0m",
        )
    return ("", "", "", "", "")


def format_depth_bar(
    size: float,
    max_size: float,
    width: int,
    *,
    fill: str = "█",
) -> str:
    """Horizontal depth meter: length ∝ ``size`` vs ``max_size`` (cap at ``width``)."""
    if width < 1:
        return ""
    if max_size <= 0 or size <= 0:
        return "░" * width
    frac = min(1.0, size / max_size)
    filled = int(round(frac * width))
    filled = min(width, max(0, filled))
    return fill * filled + "░" * (width - filled)


def term_width(stream: TextIO) -> int:
    try:
        if getattr(stream, "fileno", lambda: -1)() >= 0:
            return max(40, shutil.get_terminal_size().columns)
    except (OSError, AttributeError, ValueError):
        pass
    return 72


def content_width(stream: TextIO) -> int:
    tw = term_width(stream)
    return max(48, min(tw - 4, 88))


def center_line(out: TextIO, text: str, term_w: int) -> None:
    vis = len(strip_ansi(text))
    pad = max(0, (term_w - vis) // 2)
    out.write(f"{' ' * pad}{text}\n")


def emit_boxed_header(
    out: TextIO,
    *,
    lines: Sequence[str],
    term_w: int,
    dim: str,
    rst: str,
) -> None:
    """
    Centered rectangle: ``╔═══╗`` / ``║`` title lines ``║`` / ``╚═══╝``.

    Standard top-of-display banner: first line is the view kind (e.g. ``User``,
    ``Top holders``), second line is the primary subtitle (slug, name, etc.).

    Inner width is content-based, capped by ``term_w``, with vertical sides
    connecting top and bottom rules.
    """
    tw = max(40, term_w)
    vis_lens = [len(strip_ansi(L)) for L in lines]
    max_v = max(vis_lens) if vis_lens else 0
    inner = min(max(max_v + 8, 36), tw - 4)
    inner = max(inner, max_v)
    box_w = inner + 2
    if box_w > tw:
        inner = max(8, tw - 2)
        box_w = inner + 2
    pad = max(0, (tw - box_w) // 2)
    prefix = " " * pad

    out.write("\n")
    out.write(f"{prefix}{dim}╔{'═' * inner}╗{rst}\n")
    for line in lines:
        v = len(strip_ansi(line))
        pl = max(0, (inner - v) // 2)
        pr = inner - v - pl
        out.write(f"{prefix}{dim}║{rst}{' ' * pl}{line}{' ' * pr}{dim}║{rst}\n")
    out.write(f"{prefix}{dim}╚{'═' * inner}╝{rst}\n")
    out.write("\n")


def emit_centered_yes_no(
    out: TextIO,
    *,
    term_w: int,
    yes_price: float,
    no_price: float,
    dim: str,
    accent: str,
    rst: str,
) -> None:
    """Single centered line: Yes / No implied probabilities (primary market)."""
    y = yes_price * 100.0
    n = no_price * 100.0
    line = (
        f"{accent}Yes{rst} {dim}{y:.1f}%{rst}    {dim}·{rst}    "
        f"{accent}No{rst} {dim}{n:.1f}%{rst}"
    )
    center_line(out, line, term_w)


def emit_short_centered_separator(
    out: TextIO,
    *,
    inner_w: int,
    dim: str,
    rst: str,
    dash_fraction: float = 0.44,
) -> None:
    """Narrow rule centered within the same width as full box rules (event → markets)."""
    dash_len = max(14, int(inner_w * dash_fraction))
    total_pad = max(0, inner_w - dash_len)
    left_pad = total_pad // 2
    right_pad = total_pad - left_pad
    out.write(
        f"{' ' * left_pad}{dim}{'─' * dash_len}{rst}{' ' * right_pad}\n"
    )


def emit_horizontal_rule(
    out: TextIO,
    width: int,
    *,
    dim: str,
    rst: str,
    char: str = "─",
    label: str | None = None,
) -> None:
    if label:
        lab = f" {label} "
        if len(lab) >= width:
            out.write(f"{dim}{char * width}{rst}\n")
            return
        pad = width - len(lab)
        left = pad // 2
        right = pad - left
        out.write(f"{dim}{char * left}{rst}{lab}{dim}{char * right}{rst}\n")
    else:
        out.write(f"{dim}{char * width}{rst}\n")


def emit_menu_header(
    out: TextIO,
    *,
    tags: str | Sequence[str] | None,
    bold: str,
    dim: str,
    accent: str,
    rst: str,
    term_w: int,
) -> None:
    if isinstance(tags, str):
        tag_line = tags.strip()
    elif tags is not None:
        tag_line = ", ".join(t.strip() for t in tags if str(t).strip())
    else:
        tag_line = ""

    line_display = f"{bold}Display{rst}"
    if tag_line:
        line_events = f"{accent}Events for {tag_line}{rst}"
    else:
        line_events = f"{accent}Events{rst}"

    emit_boxed_header(
        out,
        lines=(line_display, line_events),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )


def emit_order_book_menu_header(
    out: TextIO,
    *,
    subtitle: str,
    event_slug: str,
    market_line: str,
    bold: str,
    dim: str,
    accent: str,
    rst: str,
    term_w: int,
) -> None:
    """
    Same boxed header as :func:`emit_menu_header`, then left ``Event:`` / ``Market:``.
    """
    line_title = f"{bold}Order book{rst}"
    line_sub = f"{accent}{subtitle}{rst}"

    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )
    ev = event_slug.strip() or "—"
    mk = market_line.strip() or "—"
    out.write(f"  {dim}Event:{rst} {accent}{ev}{rst}\n")
    out.write(f"  {dim}Market:{rst} {accent}{mk}{rst}\n")
    out.write("\n")


def text_budget_for_line(inner_w: int, indent_with_style: str) -> int:
    return max(8, inner_w - len(strip_ansi(indent_with_style)))


def description_char_cap(
    inner_w: int,
    first_indent: str,
    cont_indent: str,
    max_lines: int,
) -> int:
    first_w = text_budget_for_line(inner_w, first_indent)
    cont_w = text_budget_for_line(inner_w, cont_indent)
    if max_lines <= 1:
        return first_w
    return first_w + (max_lines - 1) * cont_w


def wrap_line(text: str, width: int, first_indent: str, cont_indent: str) -> list[str]:
    if not text:
        return []
    first_w = width - len(strip_ansi(first_indent))
    cont_w = width - len(strip_ansi(cont_indent))
    lines: list[str] = []
    rest = text
    use_first = first_indent
    while rest:
        chunk_w = first_w if use_first == first_indent else cont_w
        if len(rest) <= chunk_w:
            lines.append(f"{use_first}{rest}")
            break
        cut = rest.rfind(" ", 0, chunk_w + 1)
        if cut <= 0:
            cut = chunk_w
        lines.append(f"{use_first}{rest[:cut].rstrip()}")
        rest = rest[cut:].lstrip()
        use_first = cont_indent
    return lines


def market_bullet_prefixes(
    base_indent: str, desc_gray: str, dim: str, rst: str
) -> tuple[str, str, str]:
    """``- question`` line, wrapped continuation, and stats row indent (aligned)."""
    bullet = f"{base_indent}{dim}- {rst}{desc_gray}"
    text_cont = f"{' ' * len(strip_ansi(bullet))}{desc_gray}"
    stats_cont = f"{' ' * len(strip_ansi(bullet))}"
    return bullet, text_cont, stats_cont


def emit_market_list_item(
    out: TextIO,
    m: Market,
    *,
    inner_w: int,
    base_indent: str,
    show_vol: bool,
    dim: str,
    accent: str,
    desc_gray: str,
    rst: str,
) -> None:
    """One list row: ``- question`` then Yes/No (and optional vol) on the next indent."""
    title = m.question or m.slug or "(market)"
    bullet, text_cont, stats_cont = market_bullet_prefixes(
        base_indent, desc_gray, dim, rst
    )
    for line in wrap_line(title, inner_w, bullet, text_cont):
        out.write(f"{line}{rst}\n")
    odds = (
        f"{accent}Yes{rst} {dim}{m.yes_price * 100:.1f}%{rst}  ·  "
        f"{accent}No{rst} {dim}{m.no_price * 100:.1f}%{rst}"
    )
    if show_vol:
        v24 = format_vol_24h(m.volume_24h)
        odds += (
            f"  ·  {dim}vol {format_display_num(m.volume)}{rst}  ·  "
            f"24h {dim}{v24}{rst}"
        )
    out.write(f"{stats_cont}{odds}\n")
