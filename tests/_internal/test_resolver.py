"""Tests for :mod:`polymwk._internal.resolver`."""

import pytest

from polymwk.exceptions import PolymwkResolutionError
from polymwk._internal.resolver import Resolver


def test_resolver_seed_allows_token_lookup() -> None:
    r = Resolver()
    r.seed(
        "my-market",
        yes_token_id="0xyes",
        no_token_id="0xno",
        condition_id="0xcond",
    )
    assert r.get_token_id("my-market") == "0xyes"
    assert r.get_token_ids("my-market") == ("0xyes", "0xno")
    assert r.get_condition_id("my-market") == "0xcond"


def test_resolver_unseeded_raises() -> None:
    r = Resolver()
    with pytest.raises(PolymwkResolutionError):
        r.get_token_id("unknown-slug")
