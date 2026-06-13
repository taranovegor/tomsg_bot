"""
Characterization tests for DelegatingParser routing.

Each parser gets one representative URL. These tests freeze the contract:
"which URL belongs to which parser". They are the first thing to fail if a
URL pattern or delegation order changes.
"""

import pytest

from core.ports.parser import DelegatingParser
from parsers import (
    cmtt,
    habr,
    instagram,
    reddit,
    redspecial,
    tiktok,
    trashbox,
    truthsocial,
    tumblr,
    twitter,
    vk,
    youtube,
)
from parsers.instagram.cipher import Cipher as InstagramCipher

# Parser instances with minimal (stub) configuration


def _make_twitter():
    return twitter.Parser("test-agent")


def _make_instagram():
    return instagram.Parser("http://ig.test/parse", "test-agent", InstagramCipher("a" * 16))


def _make_cmtt():
    return cmtt.Parser("test-agent")


def _make_habr():
    return habr.Parser("test-agent")


def _make_reddit():
    return reddit.Parser("cid", "csecret", "test-agent (by /u/testuser)")


def _make_redspecial():
    return redspecial.Parser("test-agent")


def _make_tiktok():
    return tiktok.Parser("https://tt.test/%s.mp4", "https://tt.test/%s.jpg", "test-agent")


def _make_trashbox():
    return trashbox.Parser("test-agent")


def _make_truthsocial():
    return truthsocial.Parser("test-agent")


def _make_tumblr():
    return tumblr.Parser("tumblr-key", "test-agent")


def _make_vk():
    return vk.Parser("https://vk.test/thumb.jpg", "test-agent")


def _make_youtube():
    return youtube.Parser("yt-key", "test-agent")


def _make_delegating_parser() -> DelegatingParser:
    return DelegatingParser(
        [
            _make_cmtt(),
            _make_habr(),
            _make_instagram(),
            _make_reddit(),
            _make_redspecial(),
            _make_tiktok(),
            _make_trashbox(),
            _make_truthsocial(),
            _make_tumblr(),
            _make_twitter(),
            _make_vk(),
            _make_youtube(),
        ]
    )


# Parametrized routing table: (url, expected_parser_module_fragment)

ROUTING_TABLE = [
    (
        "https://x.com/testuser/status/1234567890",
        "parsers.twitter",
    ),
    (
        "https://twitter.com/testuser/status/9876543210",
        "parsers.twitter",
    ),
    (
        "https://www.instagram.com/p/ABC123xyz/",
        "parsers.instagram",
    ),
    (
        "https://www.instagram.com/reels/ABC123xyz/",
        "parsers.instagram",
    ),
    (
        "https://dtf.ru/tech/some-article-slug?comment=12345",
        "parsers.cmtt",
    ),
    (
        "https://vc.ru/finance/some-slug?comment=99999",
        "parsers.cmtt",
    ),
    (
        "https://habr.com/ru/articles/923922/#comment_28543112",
        "parsers.habr",
    ),
    (
        "https://www.reddit.com/r/Python/comments/abcdef/post_title/",
        "parsers.reddit",
    ),
    (
        "https://redspecial.ru/topic/example#div_comment_42",
        "parsers.redspecial",
    ),
    (
        "https://www.tiktok.com/@user/video/1234567890123456789",
        "parsers.tiktok",
    ),
    (
        "https://trashbox.ru/topic/example#div_comment_42",
        "parsers.trashbox",
    ),
    (
        "https://truthsocial.com/@user/posts/1234567890",
        "parsers.truthsocial",
    ),
    (
        "https://testblog.tumblr.com/post/123456789",
        "parsers.tumblr",
    ),
    (
        "https://vk.com/clip-12345_67890",
        "parsers.vk",
    ),
    (
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&lc=UgxTestCommentId",
        "parsers.youtube",
    ),
]

UNSUPPORTED_URLS = [
    "https://example.com/nothing",
    "https://google.com/",
    "not-a-url",
    "https://facebook.com/some/post",
]


@pytest.mark.parametrize("url", [url for url, _ in ROUTING_TABLE])
def test_delegating_parser_supports(url):
    """DelegatingParser.supports() returns True for every URL in the routing table."""
    dp = _make_delegating_parser()
    assert dp.supports(url), f"DelegatingParser did not support: {url}"


@pytest.mark.parametrize("url,expected_module", ROUTING_TABLE)
def test_routing_to_correct_parser(url, expected_module):
    """
    For each URL, exactly ONE parser claims support, and it is the expected one.

    Equality (not membership) means the test also catches URL-pattern overlap:
    if two parsers both claim a URL, DelegatingParser silently takes the first
    one — this test will fail loudly instead.
    """
    all_parsers = {
        "parsers.twitter": _make_twitter(),
        "parsers.instagram": _make_instagram(),
        "parsers.cmtt": _make_cmtt(),
        "parsers.habr": _make_habr(),
        "parsers.reddit": _make_reddit(),
        "parsers.redspecial": _make_redspecial(),
        "parsers.tiktok": _make_tiktok(),
        "parsers.trashbox": _make_trashbox(),
        "parsers.truthsocial": _make_truthsocial(),
        "parsers.tumblr": _make_tumblr(),
        "parsers.vk": _make_vk(),
        "parsers.youtube": _make_youtube(),
    }

    claiming = [mod for mod, p in all_parsers.items() if p.supports(url)]
    assert claiming == [expected_module], (
        f"Expected only {expected_module} to support {url!r}, but claimers were: {claiming}"
    )


@pytest.mark.parametrize("url", UNSUPPORTED_URLS)
def test_unsupported_urls(url):
    """DelegatingParser.supports() returns False for URLs with no matching parser."""
    dp = _make_delegating_parser()
    assert not dp.supports(url), f"DelegatingParser unexpectedly supported: {url}"


# Individual parser supports() tests (redundant with routing table, but
# explicit — each parser in isolation knows its own URLs)


class TestTwitterSupports:
    def setup_method(self):
        self.parser = _make_twitter()

    def test_x_com_url(self):
        assert self.parser.supports("https://x.com/user/status/123")

    def test_twitter_com_url(self):
        assert self.parser.supports("https://twitter.com/user/status/456")

    def test_rejects_non_status_url(self):
        assert not self.parser.supports("https://x.com/user")

    def test_rejects_instagram(self):
        assert not self.parser.supports("https://www.instagram.com/p/ABC/")


class TestInstagramSupports:
    def setup_method(self):
        self.parser = _make_instagram()

    def test_post_url(self):
        assert self.parser.supports("https://www.instagram.com/p/ABC123/")

    def test_reel_url(self):
        assert self.parser.supports("https://www.instagram.com/reels/ABC123/")

    def test_share_url(self):
        assert self.parser.supports("https://www.instagram.com/share/ABC123/")

    def test_rejects_twitter(self):
        assert not self.parser.supports("https://x.com/user/status/123")


class TestCmttSupports:
    def setup_method(self):
        self.parser = _make_cmtt()

    def test_dtf_comment_url(self):
        assert self.parser.supports("https://dtf.ru/tech/article?comment=123")

    def test_vc_comment_url(self):
        assert self.parser.supports("https://vc.ru/finance/article?comment=456")

    def test_rejects_url_without_comment(self):
        assert not self.parser.supports("https://dtf.ru/tech/article")

    def test_rejects_http_url(self):
        # CMTT regex requires https (no http:// prefix support)
        assert not self.parser.supports("http://dtf.ru/tech/article?comment=123")
