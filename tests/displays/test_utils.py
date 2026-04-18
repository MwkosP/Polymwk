"""Tests for :mod:`polymwk.displays.utils`."""

from polymwk.displays.utils import strip_ansi, wrap_line


def test_strip_ansi_removes_escape_sequences() -> None:
    s = "\033[36mhello\033[0m"
    assert strip_ansi(s) == "hello"


def test_wrap_line_respects_width() -> None:
    inner = 40
    first = "  "
    cont = "    "
    text = "one two three four five six seven"
    lines = wrap_line(text, inner, first, cont)
    assert lines
    for line in lines:
        assert len(strip_ansi(line)) <= inner
