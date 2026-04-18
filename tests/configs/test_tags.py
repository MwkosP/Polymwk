"""Tests for :mod:`polymwk.configs.tags`."""

from polymwk.configs import fetchTags, tags


def test_bitcoin_keywords_non_empty() -> None:
    assert isinstance(tags.BITCOIN, list)
    assert len(tags.BITCOIN) >= 1
    assert all(isinstance(x, str) and x for x in tags.BITCOIN)


def test_fetch_tags_matches_tag_tree() -> None:
    snap = fetchTags()
    assert snap.source == "polymwk.configs.tags"
    slugs = {c.slug for c in snap.categories}
    assert slugs == set(tags.TAG_TREE.keys())
    crypto = next(c for c in snap.categories if c.slug == "crypto")
    by_slug = {e.slug: e.keywords for e in crypto.entries}
    assert by_slug["all"] == tags.CRYPTO
    assert by_slug["bitcoin"] == tags.BITCOIN


def test_fetch_tags_all_entry_first() -> None:
    snap = fetchTags()
    for cat in snap.categories:
        assert cat.entries[0].slug == "all"
