"""
Tests for the Instagram parser (backed by yt-dlp).

yt-dlp is replaced with a fake `YoutubeDL` — no network access. Fixtures in
fixtures/instagram mirror the shape of yt-dlp info dicts for Instagram with
anonymised IDs and URLs:
  reel.json            — single video post / reel
  carousel_mixed.json  — carousel: two videos and a photo item yt-dlp could not extract (null)
"""

import json
import pathlib
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from core.domain.entity import Content, Link, Video
from core.exceptions import InvalidUrlError, ParseError
from parsers.instagram.parser import Parser as InstagramParser

_F = pathlib.Path(__file__).parent.parent / "fixtures" / "instagram"

REEL_FIXTURE = json.loads((_F / "reel.json").read_text())
CAROUSEL_FIXTURE = json.loads((_F / "carousel_mixed.json").read_text())

REEL_URL = "https://www.instagram.com/reels/ABC123xyz/"
POST_URL = "https://www.instagram.com/p/ABC123xyz/"


class FakeYoutubeDL:
    """Stands in for yt_dlp.YoutubeDL; records options, returns a canned info dict."""

    instances: list["FakeYoutubeDL"] = []
    result: dict | None = None
    errors: list[str] = []

    def __init__(self, options):
        self.options = options
        self.calls = []
        FakeYoutubeDL.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=True):
        self.calls.append((url, download))
        for msg in FakeYoutubeDL.errors:
            self.options["logger"].error(msg)
        return FakeYoutubeDL.result


@pytest.fixture
def ydl():
    FakeYoutubeDL.instances = []
    FakeYoutubeDL.result = None
    FakeYoutubeDL.errors = []
    with patch("parsers.instagram.parser.YoutubeDL", FakeYoutubeDL):
        yield FakeYoutubeDL


@pytest.fixture
def parser():
    return InstagramParser()


class TestSupports:
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.instagram.com/p/ABC123/",
            "https://www.instagram.com/reels/ABC123/",
            "https://www.instagram.com/reel/ABC123/",
            "https://www.instagram.com/share/ABC123/",
            "https://instagram.com/p/ABC123/?img_index=1",
        ],
    )
    def test_supported(self, parser, url):
        assert parser.supports(url)

    @pytest.mark.parametrize(
        "url",
        ["https://x.com/user/status/123", "https://www.instagram.com/someuser/"],
    )
    def test_unsupported(self, parser, url):
        assert not parser.supports(url)


def test_rejects_unsupported_url(parser, ydl):
    with pytest.raises(InvalidUrlError):
        parser.parse("https://www.instagram.com/someuser/")
    assert ydl.instances == []


class TestOptions:
    def test_extracts_without_download(self, parser, ydl):
        ydl.result = REEL_FIXTURE
        parser.parse(REEL_URL)
        assert ydl.instances[0].calls == [(REEL_URL, False)]

    def test_prefers_progressive_format(self, parser, ydl):
        ydl.result = REEL_FIXTURE
        parser.parse(REEL_URL)
        assert ydl.instances[0].options["format"].startswith("best[vcodec!=none][acodec!=none]")

    def test_no_proxy_by_default(self, parser, ydl):
        ydl.result = REEL_FIXTURE
        parser.parse(REEL_URL)
        assert "proxy" not in ydl.instances[0].options

    def test_proxy_passed_when_configured(self, ydl):
        ydl.result = REEL_FIXTURE
        InstagramParser(proxy="http://proxy.test:3128").parse(REEL_URL)
        assert ydl.instances[0].options["proxy"] == "http://proxy.test:3128"


class TestReel:
    @pytest.fixture
    def content(self, parser, ydl):
        ydl.result = REEL_FIXTURE
        return parser.parse(REEL_URL)

    def test_returns_content(self, content):
        assert isinstance(content, Content)
        assert content.backlink.url == REEL_URL

    def test_video(self, content):
        assert len(content.media) == 1
        video = content.media[0]
        assert isinstance(video, Video)
        assert video.resource_url == REEL_FIXTURE["url"]
        assert video.thumbnail_url == REEL_FIXTURE["thumbnail"]
        assert video.mime_type == "video/mp4"

    def test_text_is_raw_caption(self, content):
        # Sanitising is the renderer's job (shared.htmls.sanitize_html).
        assert content.text == REEL_FIXTURE["description"]

    def test_author(self, content):
        assert content.author == Link("https://www.instagram.com/some.user/", "Display Name")

    def test_created_at_is_utc(self, content):
        assert content.created_at == datetime.fromtimestamp(REEL_FIXTURE["timestamp"], UTC)
        assert content.created_at.tzinfo is UTC

    def test_metrics(self, content):
        assert content.metrics == ["💬 10", "❤️ 6K"]


def test_missing_metadata_is_none(parser, ydl):
    ydl.result = {"id": "x", "url": "https://instagram.cdn.test/v.mp4", "description": ""}
    content = parser.parse(REEL_URL)
    assert content.text is None
    assert content.author is None
    assert content.created_at is None
    assert content.metrics is None
    assert content.media[0].thumbnail_url is None


def test_author_falls_back_to_username(parser, ydl):
    ydl.result = {"url": "https://instagram.cdn.test/v.mp4", "channel": "some.user"}
    assert parser.parse(REEL_URL).author.text == "some.user"


class TestCarousel:
    @pytest.fixture
    def content(self, parser, ydl):
        ydl.result = CAROUSEL_FIXTURE
        ydl.errors = ["ERROR: [Instagram] child2: No video formats found!"]
        return parser.parse(POST_URL)

    def test_keeps_only_extracted_videos(self, content):
        assert [m.resource_url for m in content.media] == [
            "https://instagram.cdn.test/v/child1.mp4",
            "https://instagram.cdn.test/v/child3.mp4",
        ]

    def test_post_level_fields_win(self, content):
        assert content.text == "Carousel caption"
        assert content.author.url == "https://www.instagram.com/some.user/"

    def test_missing_fields_fall_back_to_first_item(self, content):
        assert content.created_at == datetime.fromtimestamp(1793636092, UTC)
        assert content.metrics == ["💬 2K", "❤️ 2M"]


class TestFailures:
    def test_photo_post(self, parser, ydl):
        ydl.errors = ["ERROR: [Instagram] ABC123xyz: There is no video in this post"]
        with pytest.raises(ParseError, match="photo posts are not supported"):
            parser.parse(POST_URL)

    def test_photo_only_carousel(self, parser, ydl):
        ydl.result = {"_type": "playlist", "channel": "some.user", "entries": [None, None]}
        ydl.errors = ["ERROR: [Instagram] c1: No video formats found!"] * 2
        with pytest.raises(ParseError, match="photo posts are not supported"):
            parser.parse(POST_URL)

    def test_other_error_is_reported(self, parser, ydl):
        ydl.errors = ["ERROR: [Instagram] ABC123xyz: Requested content is not available"]
        with pytest.raises(ParseError, match="Requested content is not available"):
            parser.parse(POST_URL)

    def test_no_data_without_errors(self, parser, ydl):
        with pytest.raises(ParseError, match="no data"):
            parser.parse(POST_URL)
