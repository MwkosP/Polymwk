"""Normalise event tag query arguments (string or sequence)."""

from collections.abc import Sequence


def normalize_event_tag_query(query: str | Sequence[str]) -> list[str]:
    """Return unique non-empty tag strings (dedupe case-insensitively, keep first spelling)."""
    items = [query] if isinstance(query, str) else list(query)
    out: list[str] = []
    seen_lower: set[str] = set()
    for raw in items:
        tag = raw.strip()
        if not tag:
            continue
        key = tag.lower()
        if key in seen_lower:
            continue
        seen_lower.add(key)
        out.append(tag)
    return out
