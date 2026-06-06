"""
Characterization tests for MessageRenderer.

These tests freeze the current output format. They cover:
- HTML escaping of text
- Timestamp formatting (including timezone behaviour as-is)
- Author link rendering
- Metric formatting
- Backlink appending
"""
from datetime import datetime, timezone, timedelta

import pytest

from core.parser.entity import Content, Link, Photo
from core.telega.renderer import MessageRenderer


@pytest.fixture
def renderer():
    return MessageRenderer()


# Minimal content

def test_render_backlink_only(renderer):
    content = Content(backlink=Link("https://x.com/u/status/1"))
    result = renderer.render(content)
    assert result == ""


def test_render_with_link_backlink_only(renderer):
    content = Content(backlink=Link("https://x.com/u/status/1"))
    result = renderer.render_with_link(content)
    assert result == "https://x.com/u/status/1"


def test_render_with_link_named_backlink(renderer):
    content = Content(backlink=Link("https://x.com/u/status/1", "Original post"))
    result = renderer.render_with_link(content)
    assert result == '<a href="https://x.com/u/status/1">Original post</a>'


# Text escaping

def test_render_plain_text(renderer):
    content = Content(backlink=Link("https://example.com"), text="Hello world")
    assert "Hello world" in renderer.render(content)


def test_render_text_escapes_ampersand(renderer):
    content = Content(backlink=Link("https://example.com"), text="A & B")
    assert "A &amp; B" in renderer.render(content)


def test_render_text_escapes_less_than(renderer):
    content = Content(backlink=Link("https://example.com"), text="a < b")
    assert "a &lt; b" in renderer.render(content)


def test_render_text_preserves_html_tags(renderer):
    """escape_non_tags passes through tag-like substrings as-is (current behaviour)."""
    content = Content(backlink=Link("https://example.com"), text="Hello <b>world</b>")
    result = renderer.render(content)
    assert "<b>world</b>" in result


def test_render_text_escapes_non_tag_angle_bracket(renderer):
    """A bare < without a closing > is treated as literal and escaped."""
    content = Content(backlink=Link("https://example.com"), text="score: <3")
    result = renderer.render(content)
    assert "&lt;3" in result


# Author

def test_render_author_link(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        author=Link("https://x.com/user", "Test User"),
    )
    result = renderer.render(content)
    assert '💁<a href="https://x.com/user">Test User</a>' in result


def test_render_author_url_only(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        author=Link("https://x.com/user"),
    )
    result = renderer.render(content)
    assert "💁https://x.com/user" in result


def test_render_author_with_special_chars_escaped(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        author=Link("https://example.com/?a=1&b=2", "Author & Co"),
    )
    result = renderer.render(content)
    assert "Author &amp; Co" in result
    assert "?a=1&amp;b=2" in result


# Timestamp

def test_render_created_at_format(renderer):
    """Timestamp uses %d.%m.%y %H:%M %Z — freeze the format as-is."""
    dt = datetime(2024, 1, 15, 9, 30, tzinfo=timezone.utc)
    content = Content(backlink=Link("https://example.com"), created_at=dt)
    result = renderer.render(content)
    assert "15.01.24 09:30 UTC" in result


def test_render_naive_datetime_no_tz_suffix(renderer):
    """Naive datetime: %Z is empty string, so no timezone label (current behaviour)."""
    dt = datetime(2024, 3, 10, 14, 0)
    content = Content(backlink=Link("https://example.com"), created_at=dt)
    result = renderer.render(content)
    # The trailing space from empty %Z is stripped by .strip()
    assert "10.03.24 14:00" in result


def test_render_author_and_created_at_on_same_line(renderer):
    """Author and timestamp are placed on the same line separated by ', '."""
    dt = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    content = Content(
        backlink=Link("https://example.com"),
        author=Link("https://x.com/u", "User"),
        created_at=dt,
    )
    result = renderer.render(content)
    first_line = result.splitlines()[0]
    assert "💁" in first_line
    assert "01.01.24 00:00 UTC" in first_line
    assert ", " in first_line


# Metrics

def test_render_metrics(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        metrics=["💬 10", "🔁 5", "❤️ 100"],
    )
    result = renderer.render(content)
    assert "💬 10  🔁 5  ❤️ 100" in result


def test_render_empty_metrics_not_shown(renderer):
    content = Content(backlink=Link("https://example.com"), metrics=[])
    result = renderer.render(content)
    assert result == ""


# Full composition

def test_render_with_link_full_content(renderer):
    """
    Full Content object → expected HTML output.
    Freezes the complete rendering contract end-to-end.
    """
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    content = Content(
        backlink=Link("https://x.com/user/status/1", "Original post"),
        author=Link("https://x.com/user", "Test User"),
        created_at=dt,
        text="Hello world",
        metrics=["💬 5", "🔁 2", "❤️ 42"],
        media=[Photo("https://example.com/img.jpg")],
    )
    result = renderer.render_with_link(content)

    assert '💁<a href="https://x.com/user">Test User</a>' in result
    assert "01.01.24 12:00 UTC" in result
    assert "Hello world" in result
    assert "💬 5  🔁 2  ❤️ 42" in result
    assert '<a href="https://x.com/user/status/1">Original post</a>' in result
