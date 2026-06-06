"""
Characterization tests for the Instagram parser.

HTTP is mocked via `responses` — no real network access.

Real fixtures fetched 2026-06-25 from api.videodropper.app/allinone:
  instagram/reel_video.json          — reel DXb_wYHDBmM  (1 video)
  instagram/post_single_photo.json   — post DU5X2F1CF_X  (1 photo; API also returns "p": true)
  instagram/post_gallery_5_photos.json — post DFfqfgXIK5O (5 photos, no "video" key)

CDN URLs contain expiry timestamps (oe=…) — they expire in weeks but tests
mock HTTP so this does not matter.
"""
import json
import pathlib

import pytest
import responses as responses_lib

from core.parser.entity import Content, Video, Photo
from core.parser.exception import ParseError
from parser.instagram.cipher import Cipher
from parser.instagram.parser import Parser as InstagramParser

_F = pathlib.Path(__file__).parent.parent / "fixtures" / "instagram"

REEL_FIXTURE    = json.loads((_F / "reel_video.json").read_text())
PHOTO_FIXTURE   = json.loads((_F / "post_single_photo.json").read_text())
GALLERY_FIXTURE = json.loads((_F / "post_gallery_5_photos.json").read_text())

PARSER_URL     = "http://instagram-parser.test/parse"
ENCRYPTION_KEY = "a" * 16

REEL_URL    = "https://www.instagram.com/reel/DXb_wYHDBmM/"
PHOTO_URL   = "https://www.instagram.com/p/DU5X2F1CF_X/"
GALLERY_URL = "https://www.instagram.com/p/DFfqfgXIK5O/"


@pytest.fixture
def parser():
    return InstagramParser(PARSER_URL, "test-agent/1.0", Cipher(ENCRYPTION_KEY))


# supports()

class TestSupports:
    def test_post_url(self, parser):
        assert parser.supports("https://www.instagram.com/p/ABC123/")

    def test_reel_url(self, parser):
        assert parser.supports("https://www.instagram.com/reels/ABC123/")

    def test_reel_url_singular(self, parser):
        assert parser.supports("https://www.instagram.com/reel/DXb_wYHDBmM/")

    def test_share_url(self, parser):
        assert parser.supports("https://www.instagram.com/share/ABC123/")

    def test_without_www(self, parser):
        assert parser.supports("https://instagram.com/p/ABC123/")

    def test_rejects_twitter(self, parser):
        assert not parser.supports("https://x.com/user/status/123")

    def test_rejects_ig_profile(self, parser):
        assert not parser.supports("https://www.instagram.com/someuser/")


# parse() — reel (1 video, real fixture)

@responses_lib.activate
def test_reel_returns_content(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=REEL_FIXTURE, status=200)
    assert isinstance(parser.parse(REEL_URL), Content)


@responses_lib.activate
def test_reel_backlink(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=REEL_FIXTURE, status=200)
    assert parser.parse(REEL_URL).backlink.url == REEL_URL


@responses_lib.activate
def test_reel_video_media(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=REEL_FIXTURE, status=200)
    content = parser.parse(REEL_URL)
    assert len(content.media) == 1
    vid = content.media[0]
    assert isinstance(vid, Video)
    assert vid.resource_url == REEL_FIXTURE["video"][0]["video"]
    assert vid.thumbnail_url == REEL_FIXTURE["video"][0]["thumbnail"]
    assert vid.mime_type == "video/mp4"


# parse() — single photo post (real fixture; API returns extra "p": true key)

@responses_lib.activate
def test_photo_returns_content(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=PHOTO_FIXTURE, status=200)
    assert isinstance(parser.parse(PHOTO_URL), Content)


@responses_lib.activate
def test_photo_backlink(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=PHOTO_FIXTURE, status=200)
    assert parser.parse(PHOTO_URL).backlink.url == PHOTO_URL


@responses_lib.activate
def test_photo_one_photo_object(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=PHOTO_FIXTURE, status=200)
    content = parser.parse(PHOTO_URL)
    assert len(content.media) == 1
    assert isinstance(content.media[0], Photo)
    assert content.media[0].resource_url == PHOTO_FIXTURE["image"][0]


@responses_lib.activate
def test_photo_unknown_p_key_ignored(parser):
    """Real API returns 'p': true alongside 'image'. Parser must not crash on unknown keys."""
    assert "p" in PHOTO_FIXTURE
    assert PHOTO_FIXTURE.get("video") is None  # no video key
    responses_lib.add(responses_lib.GET, PARSER_URL, json=PHOTO_FIXTURE, status=200)
    content = parser.parse(PHOTO_URL)
    assert len(content.media) == 1


# parse() — gallery (5 photos, real fixture; no "video" key at all)

@responses_lib.activate
def test_gallery_returns_content(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=GALLERY_FIXTURE, status=200)
    assert isinstance(parser.parse(GALLERY_URL), Content)


@responses_lib.activate
def test_gallery_five_photos(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=GALLERY_FIXTURE, status=200)
    content = parser.parse(GALLERY_URL)
    assert len(content.media) == 5
    assert all(isinstance(m, Photo) for m in content.media)


@responses_lib.activate
def test_gallery_photo_urls_match_fixture(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, json=GALLERY_FIXTURE, status=200)
    content = parser.parse(GALLERY_URL)
    for i, url in enumerate(GALLERY_FIXTURE["image"]):
        assert content.media[i].resource_url == url


@responses_lib.activate
def test_gallery_no_video_key_handled(parser):
    """Real gallery response has no 'video' key; parser uses .get('video', [])."""
    assert "video" not in GALLERY_FIXTURE
    responses_lib.add(responses_lib.GET, PARSER_URL, json=GALLERY_FIXTURE, status=200)
    content = parser.parse(GALLERY_URL)
    assert len(content.media) == 5


# Encrypted header

@responses_lib.activate
def test_sends_encrypted_url_header(parser):
    """The request must carry the encrypted URL in the Url header, not plain text."""
    responses_lib.add(responses_lib.GET, PARSER_URL, json=REEL_FIXTURE, status=200)
    parser.parse(REEL_URL)
    sent = responses_lib.calls[0].request.headers
    assert "Url" in sent
    assert sent["Url"] != REEL_URL


# Error paths

@responses_lib.activate
def test_raises_on_500(parser):
    responses_lib.add(responses_lib.GET, PARSER_URL, status=500)
    with pytest.raises(ParseError):
        parser.parse(REEL_URL)


@responses_lib.activate
def test_raises_on_empty_media(parser):
    """Response with empty video and image lists raises ParseError."""
    responses_lib.add(responses_lib.GET, PARSER_URL, json={"video": [], "image": []}, status=200)
    with pytest.raises(ParseError):
        parser.parse(REEL_URL)


@responses_lib.activate
def test_raises_on_no_media_keys(parser):
    """Response with neither video nor image key raises ParseError."""
    responses_lib.add(responses_lib.GET, PARSER_URL, json={"fetch": True}, status=200)
    with pytest.raises(ParseError):
        parser.parse(REEL_URL)
