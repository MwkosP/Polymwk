"""Tests for :func:`~polymwk.displays.events.tags.displayTags`."""

import io

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.displays.events.tags import displayTags
from polymwk.models import TagsConfigCategory, TagsConfigEntry, TagsConfigSnapshot


def test_display_tags_writes_categories_and_keywords() -> None:
    snap = TagsConfigSnapshot(
        categories=[
            TagsConfigCategory(
                slug="demo",
                entries=[
                    TagsConfigEntry(slug="all", keywords=["a", "b"]),
                    TagsConfigEntry(slug="sub", keywords=["x"]),
                ],
            )
        ]
    )
    buf = io.StringIO()
    displayTags(snap, stream=buf, wrap_width=40)
    text = buf.getvalue()
    assert "Tag keywords" in text
    assert "demo" in text
    assert "all" in text
    assert "sub" in text
    assert "a, b" in text.replace("\n", " ") or "a," in text
    assert "x" in text


def test_display_tags_rejects_wrong_type() -> None:
    with pytest.raises(PolymwkError, match="TagsConfigSnapshot"):
        displayTags("nope", stream=io.StringIO())  # type: ignore[arg-type]
