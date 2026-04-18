"""``fetchSeries`` validation and light mocking."""

from unittest.mock import MagicMock, patch

import pytest

from polymwk.exceptions import PolymwkError
from polymwk.events.series import fetchSeries


def test_fetch_series_rejects_empty_query() -> None:
    with pytest.raises(PolymwkError, match="query must contain"):
        fetchSeries("   ")


def test_fetch_series_rejects_bad_limit() -> None:
    with pytest.raises(PolymwkError, match="limit must be"):
        fetchSeries("bitcoin", limit=0)


def test_fetch_series_rejects_bad_scan_limit() -> None:
    with pytest.raises(PolymwkError, match="event_scan_limit"):
        fetchSeries("bitcoin", limit=1, event_scan_limit=0)


@patch("polymwk.events.series.fetch_raw_gamma_events_by_tags")
@patch("polymwk.events.series.collect_series_from_tagged_gamma_events")
def test_fetch_series_returns_sorted_slice(
    mock_collect: MagicMock,
    mock_fetch_raw: MagicMock,
) -> None:
    from polymarket_apis.types.gamma_types import Series as GammaSeries

    mock_fetch_raw.return_value = []
    g_lo = GammaSeries(
        id="1",
        slug="a",
        title="A",
        volume=10.0,
        volume24hr=1.0,
        liquidity=0.0,
    )
    g_hi = GammaSeries(
        id="2",
        slug="b",
        title="B",
        volume=99.0,
        volume24hr=2.0,
        liquidity=0.0,
    )
    mock_collect.return_value = [(g_lo, 1), (g_hi, 2)]

    out = fetchSeries("bitcoin", limit=1, event_scan_limit=50)
    assert len(out) == 1
    assert out[0].slug == "b"
    assert out[0].event_count == 2
