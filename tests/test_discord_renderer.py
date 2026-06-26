"""
Tests for DiscordRenderer
"""

from datetime import UTC, datetime

import pytest

from core.domain.entity import Content, Link
from platforms.discord.renderer import DiscordRenderer


@pytest.fixture
def renderer():
    return DiscordRenderer()


def test_render_backlink_only(renderer):
    content = Content(backlink=Link("https://x.com/u/status/1"))
    assert renderer.render(content) == ""


def test_render_with_link_backlink_only(renderer):
    content = Content(backlink=Link("https://x.com/u/status/1"))
    assert renderer.render_with_link(content) == "https://x.com/u/status/1"


def test_render_with_link_named_backlink(renderer):
    content = Content(backlink=Link("https://x.com/u/status/1", "Original post"))
    assert renderer.render_with_link(content) == "[Original post](https://x.com/u/status/1)"


def test_render_plain_text(renderer):
    content = Content(backlink=Link("https://example.com"), text="Hello world")
    assert "Hello world" in renderer.render(content)


def test_render_bold_html(renderer):
    content = Content(backlink=Link("https://example.com"), text="Hello <b>world</b>")
    result = renderer.render(content)
    assert "**world**" in result


def test_render_italic_html(renderer):
    content = Content(backlink=Link("https://example.com"), text="Hello <i>world</i>")
    result = renderer.render(content)
    assert "*world*" in result


def test_render_blockquote_html(renderer):
    content = Content(
        backlink=Link("https://example.com"), text="<blockquote>quoted text</blockquote>"
    )
    result = renderer.render(content)
    assert "> quoted text" in result


def test_render_anchor_html(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        text='See <a href="https://example.com/page">this page</a>',
    )
    result = renderer.render(content)
    assert "[this page](https://example.com/page)" in result


def test_render_author_link(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        author=Link("https://x.com/user", "Test User"),
    )
    result = renderer.render(content)
    assert "\U0001f481 [Test User](https://x.com/user)" in result


def test_render_author_url_only(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        author=Link("https://x.com/user"),
    )
    result = renderer.render(content)
    assert "\U0001f481 https://x.com/user" in result


def test_render_created_at_format(renderer):
    dt = datetime(2024, 1, 15, 9, 30, tzinfo=UTC)
    content = Content(backlink=Link("https://example.com"), created_at=dt)
    result = renderer.render(content)
    assert "15.01.24 09:30 UTC" in result


def test_render_author_and_created_at_on_same_line(renderer):
    dt = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    content = Content(
        backlink=Link("https://example.com"),
        author=Link("https://x.com/u", "User"),
        created_at=dt,
    )
    result = renderer.render(content)
    first_line = result.splitlines()[0]
    assert "\U0001f481" in first_line
    assert "01.01.24 00:00 UTC" in first_line


def test_render_metrics(renderer):
    content = Content(
        backlink=Link("https://example.com"),
        metrics=["\U0001f4ac 10", "\U0001f501 5", "\u2764\ufe0f 100"],
    )
    result = renderer.render(content)
    assert "\U0001f4ac 10  \U0001f501 5  \u2764\ufe0f 100" in result


def test_render_empty_metrics_not_shown(renderer):
    content = Content(backlink=Link("https://example.com"), metrics=[])
    assert renderer.render(content) == ""


def test_render_with_link_full_content(renderer):
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    content = Content(
        backlink=Link("https://x.com/user/status/1", "Original post"),
        author=Link("https://x.com/user", "Test User"),
        created_at=dt,
        text="Hello <b>world</b>",
        metrics=["\U0001f4ac 5", "\U0001f501 2", "\u2764\ufe0f 42"],
    )
    result = renderer.render_with_link(content)

    assert "\U0001f481 [Test User](https://x.com/user)" in result
    assert "01.01.24 12:00 UTC" in result
    assert "Hello **world**" in result
    assert "\U0001f4ac 5  \U0001f501 2  \u2764\ufe0f 42" in result
    assert "[Original post](https://x.com/user/status/1)" in result


def test_render_truncates_long_text(renderer):
    content = Content(
        backlink=Link("https://x.com/u/1", "s"),
        text="hello " + "x" * 500,
    )
    max_len = 50
    result = renderer.render(content, max_length=max_len)
    assert len(result) <= max_len
    assert result.endswith("...")


def test_render_max_length_noop_when_under_limit(renderer):
    content = Content(
        backlink=Link("https://x.com/u/1"),
        text="short text",
    )
    result = renderer.render_with_link(content, max_length=1024)
    assert "short text" in result
    assert not result.endswith("...")
