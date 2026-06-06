"""
Characterization tests for the Twitter/X parser.

HTTP is mocked via `responses` — no real network access.

Real fixtures fetched 2026-06-25 from api.vxtwitter.com:
  twitter/gallery_4_photos.json      — status/2000966638414241957 (4-photo gallery)
  twitter/video_single.json          — status/1882129591508296135 (single video)
  twitter/text_only.json             — status/1068183074691837954 (text only, no media)

Hand-crafted fixture kept for edge-case tests:
  twitter/crafted_photo_with_html.json — user_name with (@handle) suffix, HTML in text
"""
import json
import pathlib
from datetime import datetime, timezone

import pytest
import responses as responses_lib

from core.parser.entity import Content, Photo, Video
from core.parser.exception import ParseError, InvalidUrlError
from parser.twitter.parser import Parser as TwitterParser

_F = pathlib.Path(__file__).parent.parent / "fixtures" / "twitter"

GALLERY = json.loads((_F / "gallery_4_photos.json").read_text())
VIDEO_F = json.loads((_F / "video_single.json").read_text())
TEXT_F  = json.loads((_F / "text_only.json").read_text())
CRAFTED = json.loads((_F / "crafted_photo_with_html.json").read_text())

GALLERY_URL   = "https://x.com/AURORAmusic/status/2000966638414241957"
VIDEO_URL     = "https://x.com/AURORAmusic/status/1882129591508296135"
TEXT_URL      = "https://x.com/AURORAmusic/status/1068183074691837954"
CRAFTED_URL   = "https://x.com/testuser/status/1234567890"

def _api_url(status_id: str) -> str:
    return f"https://api.vxtwitter.com/status/{status_id}"

GALLERY_API = _api_url("2000966638414241957")
VIDEO_API   = _api_url("1882129591508296135")
TEXT_API    = _api_url("1068183074691837954")
CRAFTED_API = _api_url("1234567890")


@pytest.fixture
def parser():
    return TwitterParser("test-agent/1.0")


# supports()

class TestSupports:
    def test_x_com_status_url(self, parser):
        assert parser.supports("https://x.com/user/status/123456")

    def test_twitter_com_status_url(self, parser):
        assert parser.supports("https://twitter.com/user/status/789")

    def test_http_x_com(self, parser):
        assert parser.supports("http://x.com/user/status/123")

    def test_rejects_x_com_profile(self, parser):
        assert not parser.supports("https://x.com/user")

    def test_rejects_x_com_home(self, parser):
        assert not parser.supports("https://x.com/home")

    def test_rejects_instagram(self, parser):
        assert not parser.supports("https://www.instagram.com/p/ABC/")

    def test_rejects_non_url(self, parser):
        assert not parser.supports("just some text")


# parse() — gallery tweet (4 photos, real fixture)

@responses_lib.activate
def test_gallery_returns_content(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    assert isinstance(parser.parse(GALLERY_URL), Content)


@responses_lib.activate
def test_gallery_author(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    content = parser.parse(GALLERY_URL)
    assert content.author.url == "https://x.com/AURORAmusic"
    assert content.author.text == "AURORA"


@responses_lib.activate
def test_gallery_text(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    content = parser.parse(GALLERY_URL)
    assert content.text == GALLERY["text"]


@responses_lib.activate
def test_gallery_created_at(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    content = parser.parse(GALLERY_URL)
    assert content.created_at == datetime(2025, 12, 16, 16, 29, 57, tzinfo=timezone.utc)
    assert content.created_at.tzinfo is not None


@responses_lib.activate
def test_gallery_metrics(parser):
    # replies=31, retweets=99, likes=1115 → 1K
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    content = parser.parse(GALLERY_URL)
    assert content.metrics == ["💬 31", "🔁 99", "❤️ 1K"]


@responses_lib.activate
def test_gallery_four_photos(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    content = parser.parse(GALLERY_URL)
    assert len(content.media) == 4
    assert all(isinstance(m, Photo) for m in content.media)


@responses_lib.activate
def test_gallery_photo_urls_match_fixture(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    content = parser.parse(GALLERY_URL)
    for i, item in enumerate(GALLERY["media_extended"]):
        assert content.media[i].resource_url == item["url"]


@responses_lib.activate
def test_gallery_backlink(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, json=GALLERY, status=200)
    content = parser.parse(GALLERY_URL)
    assert "AURORAmusic" in content.backlink.url
    assert "2000966638414241957" in content.backlink.url


# parse() — video tweet (real fixture)

@responses_lib.activate
def test_video_media_type(parser):
    responses_lib.add(responses_lib.GET, VIDEO_API, json=VIDEO_F, status=200)
    content = parser.parse(VIDEO_URL)
    assert len(content.media) == 1
    assert isinstance(content.media[0], Video)


@responses_lib.activate
def test_video_mime_type(parser):
    responses_lib.add(responses_lib.GET, VIDEO_API, json=VIDEO_F, status=200)
    content = parser.parse(VIDEO_URL)
    assert content.media[0].mime_type == "video/mp4"


@responses_lib.activate
def test_video_has_thumbnail(parser):
    responses_lib.add(responses_lib.GET, VIDEO_API, json=VIDEO_F, status=200)
    content = parser.parse(VIDEO_URL)
    assert content.media[0].thumbnail_url == VIDEO_F["media_extended"][0]["thumbnail_url"]


@responses_lib.activate
def test_video_metrics(parser):
    # replies=50, retweets=808, likes=5318 → 5K
    responses_lib.add(responses_lib.GET, VIDEO_API, json=VIDEO_F, status=200)
    content = parser.parse(VIDEO_URL)
    assert content.metrics == ["💬 50", "🔁 808", "❤️ 5K"]


# parse() — text-only tweet (no media, real fixture)

@responses_lib.activate
def test_text_only_no_media(parser):
    responses_lib.add(responses_lib.GET, TEXT_API, json=TEXT_F, status=200)
    content = parser.parse(TEXT_URL)
    assert content.media == []


@responses_lib.activate
def test_text_only_text(parser):
    responses_lib.add(responses_lib.GET, TEXT_API, json=TEXT_F, status=200)
    content = parser.parse(TEXT_URL)
    assert content.text == TEXT_F["text"]


@responses_lib.activate
def test_text_only_metrics(parser):
    # replies=1082 → 1K, retweets=1255 → 1K, likes=9133 → 9K
    responses_lib.add(responses_lib.GET, TEXT_API, json=TEXT_F, status=200)
    content = parser.parse(TEXT_URL)
    assert content.metrics == ["💬 1K", "🔁 1K", "❤️ 9K"]


# parse() — edge cases using hand-crafted fixture

@responses_lib.activate
def test_handle_suffix_stripped_from_user_name(parser):
    """user_name 'Test User (@testuser)' → author.text 'Test User'."""
    responses_lib.add(responses_lib.GET, CRAFTED_API, json=CRAFTED, status=200)
    content = parser.parse(CRAFTED_URL)
    assert content.author.text == "Test User"
    assert "@testuser" not in content.author.text


@responses_lib.activate
def test_html_tags_preserved_in_text(parser):
    """Text containing <b>…</b> passes through as-is (not escaped by the parser)."""
    responses_lib.add(responses_lib.GET, CRAFTED_API, json=CRAFTED, status=200)
    content = parser.parse(CRAFTED_URL)
    assert "<b>with bold</b>" in content.text


# Error paths

@responses_lib.activate
def test_parse_raises_on_non_200(parser):
    responses_lib.add(responses_lib.GET, GALLERY_API, status=500)
    with pytest.raises(ParseError):
        parser.parse(GALLERY_URL)


def test_parse_raises_invalid_url(parser):
    with pytest.raises(InvalidUrlError):
        parser.parse("https://example.com/not-a-tweet")


# format_counter()

class TestFormatCounter:
    def test_below_1k(self):
        assert TwitterParser.format_counter(999) == "999"

    def test_exactly_1k(self):
        assert TwitterParser.format_counter(1000) == "1K"

    def test_1115_rounds_to_1k(self):
        assert TwitterParser.format_counter(1115) == "1K"

    def test_1500_rounds_to_2k(self):
        assert TwitterParser.format_counter(1500) == "2K"

    def test_5318_rounds_to_5k(self):
        assert TwitterParser.format_counter(5318) == "5K"

    def test_1m(self):
        assert TwitterParser.format_counter(1_000_000) == "1M"

    def test_2_5m(self):
        assert TwitterParser.format_counter(2_500_000) == "2M"
