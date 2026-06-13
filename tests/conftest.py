import json
import pathlib
from types import SimpleNamespace

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture
def stub_config():
    """Minimal config that satisfies all parser and service constructors."""
    return SimpleNamespace(
        version="test",
        parser_http_timeout=30,
        telegram=SimpleNamespace(bot_token="test-token", base_url=None),
        instagram=SimpleNamespace(
            parser_url="http://instagram-parser.test/parse",
            encryption_key="a" * 16,
        ),
        reddit=SimpleNamespace(
            client_id="reddit-client-id",
            client_secret="reddit-client-secret",
            app_owner_username="testuser",
        ),
        google_analytics=SimpleNamespace(
            measurement_id="G-TESTTEST",
            secret="ga-secret",
            user_identifier_salt="test-salt",
        ),
        tiktok=SimpleNamespace(
            video_resource_url="https://tiktok.test/video/%s.mp4",
            thumbnail_resource_url="https://tiktok.test/thumb/%s.jpg",
        ),
        tumblr=SimpleNamespace(api_key="tumblr-api-key"),
        vk=SimpleNamespace(thumbnail_url="https://vk.test/thumb.jpg"),
        youtube=SimpleNamespace(api_key="yt-api-key"),
    )
