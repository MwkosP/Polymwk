"""Tests for :mod:`polymwk.displays.users.user_info`."""

import io
from datetime import UTC, datetime

import pytest

from polymwk.displays.users.user_info import displayUserInfo
from polymwk.exceptions import PolymwkError
from polymwk.models import UserInfo


def test_display_user_info_writes_box_and_wallet() -> None:
    buf = io.StringIO()
    u = UserInfo(
        proxy_wallet="0xabc",
        name="Test",
        pseudonym="Pseud",
        query="0xabc",
        profile_slug="test",
        profile_url="https://polymarket.com/@test",
        created_at=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
    )
    displayUserInfo(u, stream=buf)
    s = buf.getvalue()
    assert "╔" in s
    assert "User" in s
    assert "╭" in s
    assert "Profit/Loss" in s
    assert "Joined" in s
    assert "0xabc" in s
    assert "polymarket.com" in s


def test_display_user_info_rejects_wrong_type() -> None:
    with pytest.raises(PolymwkError):
        displayUserInfo("not a UserInfo", stream=io.StringIO())  # type: ignore[arg-type]
