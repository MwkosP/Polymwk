"""Tests for :mod:`polymwk.exceptions`."""

from polymwk.exceptions import PolymwkApiError, PolymwkError, PolymwkResolutionError


def test_exception_hierarchy() -> None:
    assert issubclass(PolymwkResolutionError, PolymwkError)
    assert issubclass(PolymwkApiError, PolymwkError)
