"""
Tests for parser timeouts: every requests.get / requests.post in every parser
must pass timeout=self.timeout (from the constructor, not hardcoded) so that
a hanging external server cannot occupy a thread pool slot indefinitely, and
so the timeout is configurable from a single env var.
"""
import json
import pathlib

import pytest
import responses as responses_lib
from unittest.mock import patch

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


def _assert_timeout_in_call(mock_requests_fn, expected_timeout: int, call_index: int = 0):
    c = mock_requests_fn.call_args_list[call_index]
    assert "timeout" in c.kwargs, (
        f"requests call #{call_index} has no timeout= kwarg.\n"
        f"Full call: {c}"
    )
    assert c.kwargs["timeout"] == expected_timeout, (
        f"Expected timeout={expected_timeout}, got {c.kwargs['timeout']}"
    )


class TestTwitterTimeout:
    @responses_lib.activate
    def test_requests_get_uses_constructor_timeout(self):
        """timeout= in requests.get must come from self.timeout, not hardcoded."""
        responses_lib.add(
            responses_lib.GET,
            "https://api.vxtwitter.com/status/123",
            json={
                "user_screen_name": "user",
                "user_name": "User",
                "text": "hello",
                "replies": 0,
                "retweets": 0,
                "likes": 0,
                "date": "Thu Jan 01 00:00:00 +0000 2015",
                "media_extended": [],
            },
        )
        import requests as _requests
        from parser.twitter.parser import Parser

        with patch("parser.twitter.parser.requests.get", wraps=_requests.get) as mock_get:
            Parser("test-agent", timeout=99).parse("https://x.com/user/status/123")

        _assert_timeout_in_call(mock_get, expected_timeout=99)

    def test_default_timeout_is_thirty(self):
        from parser.twitter.parser import Parser
        assert Parser("agent").timeout == 30


class TestInstagramTimeout:
    @responses_lib.activate
    def test_requests_get_uses_constructor_timeout(self):
        responses_lib.add(
            responses_lib.GET,
            "http://ig.test/parse",
            json={"video": [{"video": "http://v/v.mp4", "thumbnail": "http://v/t.jpg"}], "image": []},
        )
        import requests as _requests
        from parser.instagram.parser import Parser
        from parser.instagram.cipher import Cipher

        with patch("parser.instagram.parser.requests.get", wraps=_requests.get) as mock_get:
            Parser(
                "http://ig.test/parse", "test-agent", Cipher("a" * 16), timeout=99
            ).parse("https://www.instagram.com/p/ABC/")

        _assert_timeout_in_call(mock_get, expected_timeout=99)

    def test_default_timeout_is_thirty(self):
        from parser.instagram.parser import Parser
        from parser.instagram.cipher import Cipher
        assert Parser("http://x.test", "agent", Cipher("a" * 16)).timeout == 30


class TestCmttTimeout:
    @responses_lib.activate
    def test_requests_get_uses_constructor_timeout(self):
        fixture = json.loads(
            (_FIXTURES / "cmtt" / "comment_text_only.json").read_text()
        )
        responses_lib.add(
            responses_lib.GET,
            "https://api.dtf.ru/v2.5/comments?commentId=49646537",
            json=fixture,
        )
        import requests as _requests
        from parser.cmtt.parser import Parser

        with patch("parser.cmtt.parser.requests.get", wraps=_requests.get) as mock_get:
            Parser("test-agent", timeout=99).parse("https://dtf.ru/life/x?comment=49646537")

        _assert_timeout_in_call(mock_get, expected_timeout=99)

    def test_default_timeout_is_thirty(self):
        from parser.cmtt.parser import Parser
        assert Parser("agent").timeout == 30


class TestContainerPassesTimeout:
    # All 12 parser service keys that must receive timeout from config.
    # If a new parser is added without wiring timeout, this list catches it.
    ALL_PARSER_KEYS = [
        "parser__cmtt",
        "parser__habr",
        "parser__instagram",
        "parser__reddit",
        "parser_redspecial",
        "parser__tiktok",
        "parser__trashbox",
        "parser__truthsocial",
        "parser__tumblr",
        "parser__twitter",
        "parser__vk",
        "parser__youtube",
    ]

    @pytest.mark.parametrize("key", ALL_PARSER_KEYS)
    def test_each_parser_receives_timeout_from_config(self, stub_config, key):
        """Every parser registered in the container must expose timeout=42 when
        config.parser_http_timeout=42. A missing timeout attribute or wrong value
        means the parser ignores PARSER_HTTP_TIMEOUT."""
        from bootstrap.container import load_container

        stub_config.parser_http_timeout = 42
        container = load_container(stub_config)

        parser = container.get(key)
        assert hasattr(parser, "timeout"), (
            f"{key}: parser has no timeout attribute — constructor param missing"
        )
        assert parser.timeout == 42, (
            f"{key}: expected timeout=42, got {parser.timeout!r} — "
            f"container factory not passing parser_http_timeout"
        )
