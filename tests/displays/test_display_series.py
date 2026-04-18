"""``displaySeries`` smoke tests."""

from io import StringIO

from polymwk.displays.events.series import displaySeries
from polymwk.models import Series


def test_display_series_empty() -> None:
    out = StringIO()
    displaySeries([], tags="bitcoin", stream=out)
    assert "no series" in out.getvalue()


def test_display_series_one_row() -> None:
    out = StringIO()
    s = Series(
        id="1",
        slug="test-series",
        title="Test Series",
        recurrence="weekly",
        volume=100.0,
        volume_24h=5.0,
        liquidity=10.0,
        event_count=3,
    )
    displaySeries(s, tags="btc", stream=out)
    body = out.getvalue()
    assert "Test Series" in body
    assert "test-series" in body
    assert "weekly" in body
    assert "3" in body
