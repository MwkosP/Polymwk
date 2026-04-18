"""Tests for :mod:`polymwk.users.info`."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from polymwk.exceptions import PolymwkError
from polymwk.users.info import fetchUserInfo


def test_fetch_user_info_rejects_empty() -> None:
    with pytest.raises(PolymwkError, match="required"):
        fetchUserInfo("")
    with pytest.raises(PolymwkError, match="required"):
        fetchUserInfo("   ")


@patch("polymwk.users.info.get_gamma_client")
def test_fetch_user_info_gamma_404_returns_minimal_user(mock_get_gamma) -> None:
    """Wallets without a Polymarket public profile page still yield :class:`UserInfo`."""
    req = MagicMock()
    resp = MagicMock()
    resp.status_code = 404
    exc = httpx.HTTPStatusError("not found", request=req, response=resp)
    mock_get_gamma.return_value.get_public_profile.side_effect = exc

    addr = "0x61270a2fbd3b5d4ef8d2c23cb8b6fb4df3bfd154"
    info = fetchUserInfo(addr, include_stats=False)

    assert info.proxy_wallet == addr
    assert info.query == addr
    assert info.profile_url == ""
    assert info.profile_slug == ""
