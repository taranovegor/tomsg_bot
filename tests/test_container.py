"""
Smoke tests for load_container().

Goal: verify that all services are registered under the correct string keys and
that the DelegatingParser sub-graph resolves without any KeyError or
initialization crash. This catches key-name mismatches (e.g. parser__cmtt vs
parser_cmtt) before they surface at runtime.
"""
import pytest

from bootstrap.container import load_container
from core.ports import DelegatingParser
from platforms.telegram.renderer import MessageRenderer


def test_load_container_returns_container(stub_config):
    """load_container() does not raise and returns a Container."""
    container = load_container(stub_config)
    assert container is not None


def test_parser_delegating_parser_resolves(stub_config):
    """
    Resolving parser_delegating_parser cascades through all 12 individual
    parser registrations. A KeyError here means a registration key mismatch.
    """
    container = load_container(stub_config)
    dp = container.get("parser_delegating_parser")
    assert isinstance(dp, DelegatingParser)


def test_parser_delegating_parser_has_all_parsers(stub_config):
    """DelegatingParser contains exactly 12 parsers (one per supported platform)."""
    container = load_container(stub_config)
    dp = container.get("parser_delegating_parser")
    assert len(dp.parsers) == 12


def test_message_renderer_resolves(stub_config):
    """telega__message_renderer resolves to a MessageRenderer."""
    container = load_container(stub_config)
    renderer = container.get("telega__message_renderer")
    assert isinstance(renderer, MessageRenderer)


def test_all_parser_keys_resolve(stub_config):
    """Every individual parser service key registered in load_container resolves."""
    parser_keys = [
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
    container = load_container(stub_config)
    for key in parser_keys:
        service = container.get(key)
        assert service is not None, f"Service {key!r} resolved to None"


def test_delegating_parser_is_singleton(stub_config):
    """Repeated get() calls return the same DelegatingParser instance (lazy singleton)."""
    container = load_container(stub_config)
    dp1 = container.get("parser_delegating_parser")
    dp2 = container.get("parser_delegating_parser")
    assert dp1 is dp2
