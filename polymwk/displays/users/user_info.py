"""Terminal view for :class:`~polymwk.models.UserInfo` — profile + PnL dashboard."""

from __future__ import annotations

import sys
from datetime import UTC
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import UserInfo
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    strip_ansi,
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


def _fmt_joined_month_year(dt) -> str:
    if dt is None:
        return "—"
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.strftime("%b %Y")


def _fmt_usd_signed_accounting(n: float | None) -> str:
    if n is None:
        return "—"
    v = float(n)
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}"


def _fmt_usd_stat_cell(n: float | None) -> str:
    if n is None:
        return "—"
    sign = "-" if n < 0 else ""
    return f"{sign}${abs(float(n)):,.2f}"


def _vis_len(s: str) -> int:
    return len(strip_ansi(s))


def _pad_vis(s: str, width: int) -> str:
    return s + " " * max(0, width - _vis_len(s))


def _trunc_plain(s: str, max_w: int) -> str:
    if max_w < 1:
        return ""
    if len(s) <= max_w:
        return s
    if max_w == 1:
        return s[0]
    return s[: max_w - 1] + "…"


def _border_colors(out: TextIO) -> tuple[str, str]:
    if getattr(out, "isatty", lambda: False)():
        return ("\033[38;5;240m", "\033[0m")
    return ("", "")


def _resample_series(values: list[float], width: int) -> list[float]:
    if not values or width < 1:
        return []
    n = len(values)
    if n <= width:
        return list(values)
    out: list[float] = []
    for i in range(width):
        lo = int(i * n / width)
        hi = int((i + 1) * n / width)
        hi = max(hi, lo + 1)
        chunk = values[lo : min(hi, n)]
        out.append(sum(chunk) / len(chunk))
    return out


def _sparkline(values: list[float], width: int) -> str:
    width = max(1, width)
    sampled = _resample_series(values, width)
    if not sampled:
        return "─" * width
    lo, hi = min(sampled), max(sampled)
    chars = "▁▂▃▄▅▆▇█"
    if hi - lo < 1e-12:
        return chars[0] * len(sampled)
    parts: list[str] = []
    for v in sampled:
        t = (v - lo) / (hi - lo)
        idx = min(7, int(t * 7.999))
        parts.append(chars[idx])
    return "".join(parts)


def _pnl_hero(out: TextIO, pnl: float | None, bold: str, dim: str, rst: str) -> str:
    if pnl is None:
        return f"{dim}—{rst}"
    s = _fmt_usd_signed_accounting(pnl)
    if not getattr(out, "isatty", lambda: False)():
        return f"{bold}{s}{rst}"
    v = float(pnl)
    if v < 0:
        return f"\033[1;91m{s}{rst}"
    if v > 0:
        return f"\033[1;92m{s}{rst}"
    return f"{dim}{s}{rst}"


def _all_badge(out: TextIO, dim: str, bold: str, rst: str, *, compact: bool) -> str:
    if compact:
        if getattr(out, "isatty", lambda: False)():
            return f"{dim}[{rst}\033[44;1;97m A \033[0m{dim}]{rst}"
        return f"{dim}[{rst}{bold}A{rst}{dim}]"
    if getattr(out, "isatty", lambda: False)():
        return f"{dim}[{rst}\033[44;1;97m ALL \033[0m{dim}]{rst}"
    return f"{dim}[{rst}{bold}ALL{rst}{dim}]"


def _has_any_stats(info: UserInfo) -> bool:
    return any(
        x is not None
        for x in (
            info.positions_value_usd,
            info.biggest_win_usd,
            info.markets_traded,
            info.profit_loss_all_usd,
        )
    )


def _box(lines: list[str], inner_w: int, bdr: str, brst: str) -> list[str]:
    top = bdr + "╭" + ("─" * inner_w) + "╮" + brst
    mid = [
        bdr + "│" + brst + _pad_vis(row, inner_w) + bdr + "│" + brst for row in lines
    ]
    bot = bdr + "╰" + ("─" * inner_w) + "╯" + brst
    return [top, *mid, bot]


def _card_row_vis_width(inner_w: int) -> int:
    """Visible columns: ``│`` + inner + ``│``."""
    return inner_w + 2


def _left_stat_lines(
    info: UserInfo,
    left_w: int,
    *,
    bold: str,
    dim: str,
    accent: str,
    rst: str,
) -> list[str]:
    pv = _fmt_usd_stat_cell(info.positions_value_usd)
    bw = _fmt_usd_stat_cell(info.biggest_win_usd)
    pr = (
        str(info.markets_traded)
        if info.markets_traded is not None
        else "—"
    )
    name = clip_text(info.name or info.pseudonym or "—", max(4, left_w - 4))
    avatar = f"{accent}●{rst}"
    row_name = f"{avatar} {bold}{name}{rst}"
    views = "—"
    sub_plain = f"Joined {_fmt_joined_month_year(info.created_at)} · {views} views"
    if len(sub_plain) > left_w:
        sub_plain = _trunc_plain(sub_plain, left_w)
    sub = f"{dim}{sub_plain}{rst}"

    lines = [row_name, sub, ""]

    # Three columns: w1 + 1 + w2 + 1 + w3 == left_w
    if left_w >= 28:
        avail = left_w - 2
        w1 = max(3, avail // 3)
        w2 = max(3, (avail - w1) // 2)
        w3 = avail - w1 - w2
        w3 = max(3, w3)
        while w1 + w2 + w3 > avail:
            if w1 >= w2 and w1 > 3:
                w1 -= 1
            elif w2 > 3:
                w2 -= 1
            elif w3 > 3:
                w3 -= 1
            else:
                break
        c1 = _trunc_plain(pv, w1)
        c2 = _trunc_plain(bw, w2)
        c3 = _trunc_plain(pr, w3)
        r1 = (
            f"{bold}{_pad_plain(c1, w1)}{rst}{dim}│{rst}"
            f"{bold}{_pad_plain(c2, w2)}{rst}{dim}│{rst}"
            f"{bold}{_pad_plain(c3, w3)}{rst}"
        )
        l1 = _trunc_plain("Positions", w1)
        l2 = _trunc_plain("Biggest win", w2)
        l3 = _trunc_plain("Predictions", w3)
        r2 = (
            f"{dim}{_pad_plain(l1, w1)}│{_pad_plain(l2, w2)}│{_pad_plain(l3, w3)}{rst}"
        )
        lines.extend([r1, r2])
    else:
        lines.extend(
            [
                f"{bold}{pv}{rst} {dim}· positions{rst}",
                f"{bold}{bw}{rst} {dim}· biggest win{rst}",
                f"{bold}{pr}{rst} {dim}· predictions{rst}",
            ]
        )
    return lines


def _pad_plain(s: str, w: int) -> str:
    return s + " " * max(0, w - len(s))


def _emit_profile_pnl_dashboard(
    info: UserInfo,
    out: TextIO,
    *,
    bold: str,
    dim: str,
    accent: str,
    rst: str,
    term_w: int,
    indent: str,
) -> None:
    bdr, brst = _border_colors(out)
    gap = "  "
    I = len(indent)
    G = len(gap)
    # Per row: indent + (|+left+|) + gap + (|+right+|)  →  I + left + right + G + 4
    budget = term_w - I - G - 4
    if budget < 24:
        _emit_profile_pnl_stacked(
            info, out, bold=bold, dim=dim, accent=accent, rst=rst, term_w=term_w, indent=indent
        )
        return

    left_w = budget // 2
    right_w = budget - left_w
    MIN = 18
    if left_w < MIN or right_w < MIN:
        _emit_profile_pnl_stacked(
            info, out, bold=bold, dim=dim, accent=accent, rst=rst, term_w=term_w, indent=indent
        )
        return

    left_inner = _left_stat_lines(
        info, left_w, bold=bold, dim=dim, accent=accent, rst=rst
    )
    left_lines = _box(left_inner, left_w, bdr, brst)

    compact_badge = right_w < 26
    badge = _all_badge(out, dim, bold, rst, compact=compact_badge)
    badge_w = _vis_len(badge)
    room = max(0, right_w - badge_w)
    lab_txt = "▼ Profit/Loss" if right_w >= 28 else "▼ P/L" if right_w >= 20 else "P/L"
    if room <= 0:
        hdr_core = _pad_vis(badge, right_w)
    elif room == 1:
        one = _trunc_plain(lab_txt, 1)
        hdr_core = f"{dim}{one}{rst}" + badge
    else:
        lab_max = room - 1
        lab_txt = _trunc_plain(lab_txt, lab_max)
        pnl_label = f"{dim}{lab_txt}{rst}"
        hdr_core = _pad_vis(pnl_label, lab_max) + " " + badge
        while _vis_len(hdr_core) > right_w and len(lab_txt) > 1:
            lab_txt = _trunc_plain(lab_txt, len(lab_txt) - 1)
            pnl_label = f"{dim}{lab_txt}{rst}"
            lab_max = room - 1
            hdr_core = _pad_vis(pnl_label, lab_max) + " " + badge
        if _vis_len(hdr_core) > right_w:
            lab_max = room
            lab_txt = _trunc_plain(
                "▼ Profit/Loss" if right_w >= 28 else "▼ P/L" if right_w >= 20 else "P/L",
                lab_max,
            )
            pnl_label = f"{dim}{lab_txt}{rst}"
            hdr_core = _pad_vis(pnl_label, lab_max) + badge
    hdr = _pad_vis(hdr_core, right_w)

    hero = _pnl_hero(out, info.profit_loss_all_usd, bold, dim, rst)
    if _vis_len(hero) > right_w:
        plain = _fmt_usd_signed_accounting(info.profit_loss_all_usd)
        hero = f"{bold}{_trunc_plain(plain, right_w)}{rst}"

    sub_pl = _pad_vis(f"{dim}All-Time{rst}", right_w)
    spark_w = min(right_w, max(4, right_w))
    spark_body = (
        _sparkline(info.pnl_history, spark_w)
        if info.pnl_history
        else "─" * spark_w
    )
    spark_body = _trunc_plain(spark_body, spark_w)
    spark_body = spark_body + " " * max(0, spark_w - len(spark_body))
    spark = f"{accent}{spark_body}{rst}"
    spark_line = _pad_vis(spark, right_w)

    hero_line = _pad_vis(hero, right_w)

    right_inner = [hdr, "", hero_line, sub_pl, "", spark_line]
    right_lines = _box(right_inner, right_w, bdr, brst)

    n = max(len(left_lines), len(right_lines))
    empty_left = bdr + "│" + brst + " " * left_w + bdr + "│" + brst
    empty_right = bdr + "│" + brst + " " * right_w + bdr + "│" + brst
    while len(left_lines) < n:
        left_lines.insert(-1, empty_left)
    while len(right_lines) < n:
        right_lines.insert(-1, empty_right)

    for l_line, r_line in zip(left_lines, right_lines, strict=True):
        out.write(f"{indent}{l_line}{gap}{r_line}\n")


def _emit_profile_pnl_stacked(
    info: UserInfo,
    out: TextIO,
    *,
    bold: str,
    dim: str,
    accent: str,
    rst: str,
    term_w: int,
    indent: str,
) -> None:
    """Single-column cards: width follows terminal (clamped)."""
    bdr, brst = _border_colors(out)
    I = len(indent)
    inner = max(20, min(term_w - I - 2, 78))

    left_block = _left_stat_lines(info, inner, bold=bold, dim=dim, accent=accent, rst=rst)
    for line in _box(left_block, inner, bdr, brst):
        out.write(f"{indent}{line}\n")
    out.write("\n")

    compact_badge = inner < 28
    badge = _all_badge(out, dim, bold, rst, compact=compact_badge)
    spark_w = min(inner, max(4, inner))
    spark_body = (
        _sparkline(info.pnl_history, spark_w)
        if info.pnl_history
        else "─" * spark_w
    )
    spark_body = _trunc_plain(spark_body, spark_w).ljust(spark_w)
    spark = f"{accent}{spark_body}{rst}"

    hdr = _pad_vis(f"{dim}▼ Profit/Loss{rst}  {badge}", inner)
    if _vis_len(hdr) > inner:
        hdr = f"{dim}P/L{rst} {badge}"
        hdr = _pad_vis(hdr, inner)

    hero = _pnl_hero(out, info.profit_loss_all_usd, bold, dim, rst)
    if _vis_len(hero) > inner:
        plain = _fmt_usd_signed_accounting(info.profit_loss_all_usd)
        hero = f"{bold}{_trunc_plain(plain, inner)}{rst}"

    rows2 = [
        hdr,
        "",
        _pad_vis(hero, inner),
        _pad_vis(f"{dim}All-Time{rst}", inner),
        "",
        _pad_vis(spark, inner),
    ]
    for line in _box(rows2, inner, bdr, brst):
        out.write(f"{indent}{line}\n")


def displayUserInfo(
    info: UserInfo,
    *,
    stream: TextIO | None = None,
) -> None:
    """Profile + PnL dashboard (responsive), then wallet / links / bio."""
    out = stream if stream is not None else sys.stdout
    if not isinstance(info, UserInfo):
        raise PolymwkError("displayUserInfo expects polymwk.models.UserInfo")

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner_w = max(40, min(term_w - 2, 120))
    base = "  "
    indent = base

    sub = ((info.name or "").strip() or (info.pseudonym or "").strip())
    if not sub:
        sub = clip_text(info.proxy_wallet, 42) or "—"
    else:
        sub = clip_text(sub, 48)
    emit_boxed_header(
        out,
        lines=(f"{bold}User{rst}", f"{accent}{sub}{rst}"),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    if _has_any_stats(info) or info.name or info.pseudonym:
        I = len(indent)
        G = 2
        budget = term_w - I - G - 4
        use_side_by_side = budget >= 44 and budget // 2 >= 18 and (budget - budget // 2) >= 18

        if use_side_by_side:
            _emit_profile_pnl_dashboard(
                info,
                out,
                bold=bold,
                dim=dim,
                accent=accent,
                rst=rst,
                term_w=term_w,
                indent=indent,
            )
        else:
            _emit_profile_pnl_stacked(
                info,
                out,
                bold=bold,
                dim=dim,
                accent=accent,
                rst=rst,
                term_w=term_w,
                indent=indent,
            )
        out.write("\n")

    out.write(
        f"{indent}{dim}proxyWallet:{rst} {accent}{info.proxy_wallet}{rst}\n"
        f"{indent}{dim}query:{rst} {dim}{clip_text(info.query, inner_w - 14) or '—'}{rst}\n"
    )
    if info.profile_url:
        out.write(f"{indent}{dim}profile:{rst} {accent}{info.profile_url}{rst}\n")
    if info.x_username:
        out.write(
            f"{indent}{dim}X / Twitter:{rst} {accent}@{clip_text(info.x_username, 64)}{rst}\n"
        )
    if info.profile_image:
        out.write(
            f"{indent}{dim}image:{rst} {dim}{clip_text(info.profile_image, inner_w - 10)}{rst}\n"
        )
    out.write("\n")

    bio = (info.bio or "").strip()
    if bio:
        emit_horizontal_rule(out, min(inner_w, 72), dim=dim, rst=rst, label="Bio")
        out.write("\n")
        bi = f"{base}{dim}"
        for line in wrap_line(bio, inner_w, bi, bi):
            out.write(f"{line}{rst}\n")
        out.write("\n")

    if info.identities:
        emit_horizontal_rule(out, min(inner_w, 72), dim=dim, rst=rst, label="Identities")
        out.write("\n")
        for ident in info.identities:
            flags = []
            if ident.creator:
                flags.append("creator")
            if ident.mod:
                flags.append("mod")
            if ident.community_mod:
                flags.append("community_mod")
            fl = ", ".join(flags) if flags else "—"
            out.write(
                f"{base}{dim}id:{rst} {accent}{clip_text(ident.id, 48)}{rst}  "
                f"{dim}{fl}{rst}\n"
            )
        out.write("\n")
