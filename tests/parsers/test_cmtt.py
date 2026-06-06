"""
Characterization tests for the CMTT parser (dtf.ru / vc.ru comments).

HTTP is mocked via `responses` — no real network access.

Real fixtures fetched 2026-06-25 from api.dtf.ru/v2.5/comments:
  cmtt/comment_text_only.json  — commentId=49646537 (text, 4 reactions)
  cmtt/comment_with_image.json — commentId=50739994 (PNG image, stored for future tests)
  cmtt/comment_with_gif.json   — commentId=49624164 (GIF with isVideo=true, stored for future tests)
"""
import json
import pathlib
from datetime import datetime

import pytest
import responses as responses_lib

from core.parser.entity import Content, Link
from core.parser.exception import ParseError
from parser.cmtt.parser import Parser as CmttParser

FIXTURE = json.loads(
    (pathlib.Path(__file__).parent.parent / "fixtures" / "cmtt" / "comment_text_only.json").read_text()
)

COMMENT_ID = 49646537
DTF_URL = f"https://dtf.ru/life/3626060-chatgpt-pytaetsya-svesti-menya-s-uma-eto-massovoe-yavlenie?comment={COMMENT_ID}"
VC_URL = f"https://vc.ru/finance/some-slug?comment={COMMENT_ID}"
DTF_API = f"https://api.dtf.ru/v2.5/comments?commentId={COMMENT_ID}"
VC_API = f"https://api.vc.ru/v2.5/comments?commentId={COMMENT_ID}"


@pytest.fixture
def parser():
    return CmttParser("test-agent/1.0")


# supports()

class TestSupports:
    def test_dtf_comment_url(self, parser):
        assert parser.supports(DTF_URL)

    def test_vc_comment_url(self, parser):
        assert parser.supports(VC_URL)

    def test_rejects_dtf_without_comment(self, parser):
        assert not parser.supports("https://dtf.ru/tech/some-article")

    def test_rejects_http_scheme(self, parser):
        # The regex anchors on https, not http
        assert not parser.supports(f"http://dtf.ru/tech/article?comment={COMMENT_ID}")

    def test_rejects_unknown_domain(self, parser):
        assert not parser.supports(f"https://example.com/article?comment={COMMENT_ID}")

    def test_rejects_twitter(self, parser):
        assert not parser.supports("https://x.com/user/status/123")


# parse() — happy path with mocked HTTP (real fixture)

@responses_lib.activate
def test_parse_dtf_returns_content(parser):
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    result = parser.parse(DTF_URL)
    assert isinstance(result, Content)


@responses_lib.activate
def test_parse_author(parser):
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    assert isinstance(content.author, Link)
    assert content.author.text == "ch35h1r3 c4t"
    assert "1530880" in content.author.url


@responses_lib.activate
def test_parse_text(parser):
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    assert content.text == "Снятся ли автоматическим обезьянам шершавые кабаны 🐗🙈🙉🙊"


@responses_lib.activate
def test_parse_created_at_is_datetime(parser):
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    assert isinstance(content.created_at, datetime)


@responses_lib.activate
def test_parse_created_at_value(parser):
    """
    Parser uses datetime.fromtimestamp() — naive local time.
    Compare with fromtimestamp() of the same raw value so the test is
    timezone-agnostic and characterizes the actual behaviour as-is.
    """
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    raw_ts = FIXTURE["result"]["items"][0]["date"]
    assert content.created_at == datetime.fromtimestamp(raw_ts)


@responses_lib.activate
def test_parse_reactions_known_emoji(parser):
    """
    Only reactions with count > 0 AND id in REACTIONS_EMOJIS appear in metrics.
    Real fixture has: id=22 (😎, 40), id=4 (😂, 14), id=1 (❤️, 2), id=2 (🔥, 1).
    Many other ids have count=0 and must be absent.
    """
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    assert "😎 40" in content.metrics
    assert "😂 14" in content.metrics
    assert "❤️ 2" in content.metrics
    assert "🔥 1" in content.metrics


@responses_lib.activate
def test_parse_reactions_zero_count_excluded(parser):
    """Reactions with count=0 are filtered out regardless of id."""
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    # id=41 is 💊 in REACTIONS_EMOJIS but count=0 in fixture
    assert not any("💊" in m for m in content.metrics)
    # id=9 is 🍿 but count=0
    assert not any("🍿" in m for m in content.metrics)


@responses_lib.activate
def test_parse_backlink_contains_comment_id(parser):
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    assert str(COMMENT_ID) in content.backlink.url
    assert content.backlink.text == "ChatGPT пытается свести меня с ума. Это массовое явление"


@responses_lib.activate
def test_parse_backlink_contains_article_id(parser):
    responses_lib.add(responses_lib.GET, DTF_API, json=FIXTURE, status=200)
    content = parser.parse(DTF_URL)
    assert "3626060" in content.backlink.url


@responses_lib.activate
def test_parse_vc_domain(parser):
    """Parser works for vc.ru and calls the correct API endpoint."""
    responses_lib.add(responses_lib.GET, VC_API, json=FIXTURE, status=200)
    content = parser.parse(VC_URL)
    assert isinstance(content, Content)
    assert "vc.ru" in content.author.url


@responses_lib.activate
def test_parse_raises_on_500(parser):
    responses_lib.add(responses_lib.GET, DTF_API, status=500)
    with pytest.raises(ParseError):
        parser.parse(DTF_URL)


@responses_lib.activate
def test_parse_raises_when_comment_not_in_response(parser):
    """If the API returns items but none matches comment_id, ParseError is raised."""
    fixture_wrong_id = {
        "message": "",
        "result": {
            "items": [
                {
                    **FIXTURE["result"]["items"][0],
                    "id": 99999999,  # different id
                }
            ]
        },
    }
    responses_lib.add(responses_lib.GET, DTF_API, json=fixture_wrong_id, status=200)
    with pytest.raises(ParseError):
        parser.parse(DTF_URL)
