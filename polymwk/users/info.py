"""User-facing entry: :func:`fetchUserInfo` (profile + optional Data API stats)."""

from __future__ import annotations

import httpx
from polymarket_apis.types.common import EthAddress

from polymwk.exceptions import PolymwkApiError, PolymwkError
from polymwk.models import UserInfo
from polymwk._internal.gamma import get_gamma_client
from polymwk.users import utils as user_utils


def fetchUserInfo(user: str, *, include_stats: bool = True) -> UserInfo:
    """
    Load **public profile** data for a Polymarket user.

    ``user`` may be:

    * A **proxy wallet** ``0x…`` (42-char hex), e.g. the address shown on the site.
    * A **username** or ``@username`` (e.g. ``reflex102``), resolved via Gamma search
      / leaderboard to a proxy wallet, then ``GET /public-profile``.

    The returned :class:`~polymwk.models.UserInfo` includes ``profile_url`` when a slug
    is known (from the query or from resolution).

    If Gamma returns **404** for ``/public-profile`` (wallet has no Polymarket profile
    page yet), a minimal :class:`~polymwk.models.UserInfo` is still returned with
    ``proxy_wallet`` and ``query`` set; optional Data API stats are filled when
    ``include_stats`` is True.

    When ``include_stats`` is True (default), fills **positions value**, **biggest win**
    (max realized PnL among returned closed positions), **markets traded** (prediction
    count), and **all-time profit/loss** from the Data / leaderboard APIs — same idea as
    the site summary (not the 1D/1W/1M chart toggles). **Profile views** are not
    available on these endpoints and stay unset.
    """
    raw = (user or "").strip()
    if not raw:
        raise PolymwkError("user is required for fetchUserInfo")

    profile_slug = ""
    if user_utils.is_proxy_wallet_address(raw):
        proxy = user_utils.normalized_proxy_wallet(raw)
        q = proxy
    else:
        proxy, profile_slug = user_utils.resolve_handle_to_proxy_wallet(raw)
        q = raw

    gamma = get_gamma_client()
    try:
        prof = gamma.get_public_profile(EthAddress(proxy))
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            info = user_utils.minimal_user_info(proxy, q)
            if include_stats:
                info = info.model_copy(update=user_utils.enrich_user_stats(proxy))
            return info
        raise PolymwkApiError("Gamma public-profile request failed") from exc
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma public-profile request failed") from exc

    if not profile_slug:
        if prof.name:
            profile_slug = prof.name.strip().lower()
        elif prof.pseudonym:
            profile_slug = prof.pseudonym.strip().lower()

    info = user_utils.user_info_from_profile(prof, query=q, profile_slug=profile_slug)
    if include_stats:
        info = info.model_copy(update=user_utils.enrich_user_stats(proxy))
    return info
