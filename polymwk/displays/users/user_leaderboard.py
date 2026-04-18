"""Print leaderboard views: single-user rank and full leaderboard table."""

from __future__ import annotations

import sys
from typing import TextIO

from polymwk.exceptions import PolymwkError
from polymwk.models import (
    LeaderboardEntry,
    UserLeaderboardRank,
    UsersLeaderboardSnapshot,
)
from polymwk.displays.utils import (
    clip_text,
    emit_boxed_header,
    emit_horizontal_rule,
    format_display_num,
    term_style,
    term_width,
)

_WINDOW_LABEL: dict[str, str] = {
    "1d": "1 day",
    "7d": "7 days",
    "30d": "30 days",
    "all": "All-time",
}


def _fmt_dollar(n: float) -> str:
    sign = "-" if n < 0 else ""
    return f"{sign}${format_display_num(abs(n))}"


def displayUserLeaderboardRank(
    snapshot: UserLeaderboardRank,
    *,
    stream: TextIO | None = None,
) -> None:
    """Pretty-print rank, window, ranked metric, and optional cross metric (profit ↔ volume)."""
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, UserLeaderboardRank):
        raise PolymwkError(
            "displayUserLeaderboardRank expects polymwk.models.UserLeaderboardRank"
        )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)

    display_name = (
        (snapshot.name or "").strip()
        or (snapshot.pseudonym or "").strip()
        or clip_text(snapshot.proxy_wallet, 20)
    )
    line_title = f"{bold}Leaderboard{rst}"
    line_sub = f"{accent}{display_name}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    wlab = _WINDOW_LABEL.get(snapshot.window, snapshot.window)
    mlab = "Profit (PnL)" if snapshot.metric == "profit" else "Volume"
    out.write(f"  {dim}wallet:{rst} {accent}{clip_text(snapshot.proxy_wallet, 66)}{rst}\n")
    out.write(f"  {dim}ranked by:{rst} {bold}{mlab}{rst} {dim}·{rst} {dim}{wlab}{rst}\n\n")

    out.write(f"  {dim}Rank:{rst}     {bold}#{snapshot.rank:,}{rst}\n")
    out.write(f"  {dim}{mlab}:{rst}  {accent}{_fmt_dollar(snapshot.ranked_amount)}{rst}\n")

    if snapshot.other_metric_amount is not None:
        olab = "Volume" if snapshot.metric == "profit" else "Profit (PnL)"
        out.write(
            f"  {dim}{olab}:{rst}   {accent}{_fmt_dollar(snapshot.other_metric_amount)}{rst}\n"
        )

    if (snapshot.bio or "").strip():
        out.write(f"\n  {dim}bio:{rst} {dim}{clip_text(snapshot.bio.strip(), 72)}{rst}\n")

    out.write("\n")


_TIMEFRAME_LINE: dict[str, str] = {
    "today": "Today",
    "weekly": "Weekly",
    "monthly": "Monthly",
    "all": "All",
}


def _leaderboard_entry_display_name(entry: LeaderboardEntry) -> str:
    """Username when present; otherwise shortened ``0x…`` like the site."""
    u = entry.username.strip()
    if u and not u.startswith("0x"):
        suf = " ✓" if entry.verified_badge else ""
        return f"{u}{suf}"
    w = entry.proxy_wallet
    if len(w) > 16:
        return f"{w[:8]}…{w[-6:]}"
    return w


def _fmt_usd_commas_int(n: float) -> str:
    v = int(round(abs(n)))
    return f"{v:,}"


def _fmt_leaderboard_pnl(n: float) -> str:
    if n > 0:
        return f"+${_fmt_usd_commas_int(n)}"
    if n < 0:
        return f"-${_fmt_usd_commas_int(n)}"
    return "$0"


def _fmt_leaderboard_vol(n: float) -> str:
    """Site shows an em dash when volume is absent/zero for some rows."""
    if n == 0:
        return "—"
    return f"${_fmt_usd_commas_int(n)}"


def _rank_cell(rank: int) -> str:
    if rank == 1:
        return f"{rank} 🥇"
    if rank == 2:
        return f"{rank} 🥈"
    if rank == 3:
        return f"{rank} 🥉"
    return str(rank)


def displayUsersLeaderboard(
    snapshot: UsersLeaderboardSnapshot,
    *,
    stream: TextIO | None = None,
) -> None:
    """
    Pretty-print :class:`~polymwk.models.UsersLeaderboardSnapshot` like the Polymarket
    leaderboard UI: timeframe, category, sort hint, then rank / user / PnL / volume.
    """
    out = stream if stream is not None else sys.stdout
    if not isinstance(snapshot, UsersLeaderboardSnapshot):
        raise PolymwkError(
            "displayUsersLeaderboard expects polymwk.models.UsersLeaderboardSnapshot"
        )

    bold, dim, accent, rst = term_style(out)
    term_w = term_width(out)
    inner_w = min(96, max(56, term_w - 4))

    tf = _TIMEFRAME_LINE.get(snapshot.timeframe, snapshot.timeframe)
    cat = (snapshot.category_label or snapshot.category or "All categories").strip()
    line_title = f"{bold}Leaderboard{rst}"
    line_sub = f"{accent}{tf}{rst} {dim}·{rst} {dim}{cat}{rst}"
    emit_boxed_header(
        out,
        lines=(line_title, line_sub),
        term_w=term_w,
        dim=dim,
        rst=rst,
    )

    sort_lab = "Profit/Loss" if snapshot.order_by == "pnl" else "Volume"
    out.write(f"  {dim}Sorted by:{rst} {bold}{sort_lab}{rst}\n\n")

    if not snapshot.entries:
        out.write(f"  {dim}(no rows){rst}\n\n")
        return

    rank_w = 10
    pnl_w = 16
    vol_w = 16
    name_w = max(18, min(36, inner_w - (rank_w + 2 + pnl_w + 2 + vol_w + 6)))

    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    out.write(f"  {dim}{'#':<{rank_w}}{rst}  {dim}{'User':<{name_w}}{rst}  ")
    if snapshot.order_by == "pnl":
        out.write(f"{bold}{'Profit/Loss':>{pnl_w}}{rst}  {dim}{'Volume':>{vol_w}}{rst}\n")
    else:
        out.write(f"{dim}{'Profit/Loss':>{pnl_w}}{rst}  {bold}{'Volume':>{vol_w}}{rst}\n")
    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)

    for e in snapshot.entries:
        rk = _rank_cell(e.rank)
        name = clip_text(_leaderboard_entry_display_name(e), name_w)
        pnl_s = _fmt_leaderboard_pnl(e.pnl)
        vol_s = _fmt_leaderboard_vol(e.volume_usd)
        out.write(
            f"  {dim}{rk:<{rank_w}}{rst}  {accent}{name:<{name_w}}{rst}  "
            f"{accent}{pnl_s:>{pnl_w}}{rst}  {dim}{vol_s:>{vol_w}}{rst}\n"
        )

    emit_horizontal_rule(out, inner_w, dim=dim, rst=rst)
    out.write("\n")
