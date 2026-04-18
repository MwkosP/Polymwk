"""Event comment threads (Gamma ``GET /comments``)."""

from __future__ import annotations

from typing import Any

import httpx

from polymwk.exceptions import PolymwkApiError
from polymwk.models import Event, EventCommentsSnapshot
from polymwk._internal.gamma import get_gamma_client
from polymwk.events.utils import (
    event_comments_snapshot_from_gamma_json,
    resolve_gamma_event_for_comments,
)


def _gamma_get_comments_json(
    event_id: int,
    *,
    limit: int,
    offset: int,
    order: str | None,
    ascending: bool,
    get_positions: bool | None,
    holders_only: bool | None,
) -> list[dict[str, Any]]:
    """Raw JSON list — avoids vendor ``Comment`` validation on partial ``reactions``."""
    gamma = get_gamma_client()
    params: dict[str, str | int] = {
        "parent_entity_type": "Event",
        "parent_entity_id": event_id,
        "limit": limit,
        "offset": offset,
    }
    if order:
        params["order"] = order
        params["ascending"] = str(ascending).lower()
    if get_positions is not None:
        params["get_positions"] = str(get_positions).lower()
    if holders_only is not None:
        params["holders_only"] = str(holders_only).lower()
    r = gamma.client.get(gamma._build_url("/comments"), params=params)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def fetchEventComments(
    event: str | int | Event,
    *,
    limit: int = 50,
    offset: int = 0,
    order: str | None = "createdAt",
    ascending: bool = False,
    get_positions: bool | None = None,
    holders_only: bool | None = None,
) -> EventCommentsSnapshot:
    """
    Load comments for one **event** (top-level and replies in one list).

    Pass a polymwk :class:`~polymwk.models.Event`, a Gamma **numeric id** as ``int`` or
    digit string, or an **event slug**. Uses ``parent_entity_type=Event`` on Gamma.

    ``limit`` / ``offset`` paginate (Gamma may return slightly more or fewer rows than
    ``limit``). Default sort is **newest first** (``order=createdAt``, ``ascending=False``).
    """
    eid, slug, title = resolve_gamma_event_for_comments(event)
    try:
        raw = _gamma_get_comments_json(
            eid,
            limit=limit,
            offset=offset,
            order=order,
            ascending=ascending,
            get_positions=get_positions,
            holders_only=holders_only,
        )
    except httpx.HTTPError as exc:
        raise PolymwkApiError("Gamma /comments request failed") from exc

    return event_comments_snapshot_from_gamma_json(eid, slug, title, raw)
