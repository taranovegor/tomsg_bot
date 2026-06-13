"""
Smoke tests for load_container().

Goal: verify that all services are registered under the correct string keys and
that the DelegatingParser sub-graph resolves without any KeyError or
initialization crash. This catches key-name mismatches before they surface
at runtime.
"""

from bootstrap import keys
from bootstrap.container import load_container
from core.ports import DelegatingParser
from platforms.telegram.renderer import MessageRenderer

EXPECTED_PARSERS = {
    "cmtt",
    "habr",
    "instagram",
    "reddit",
    "redspecial",
    "tiktok",
    "trashbox",
    "truthsocial",
    "tumblr",
    "twitter",
    "vk",
    "youtube",
}


def test_load_container_returns_container(stub_config):
    """load_container() does not raise and returns a Container."""
    container = load_container(stub_config)
    assert container is not None


def test_parser_delegating_resolves(stub_config):
    """
    Resolving parser_delegating cascades through all individual parser
    registrations. A KeyError here means a registration key mismatch.
    """
    container = load_container(stub_config)
    dp = container.get(keys.PARSER_DELEGATING)
    assert isinstance(dp, DelegatingParser)


def test_delegating_contains_expected_parsers(stub_config):
    """
    Every parser in EXPECTED_PARSERS must be present in DelegatingParser's
    list. A missing parser (broken import, missing @register) is caught by
    set comparison — not just a tautological count check.
    """
    container = load_container(stub_config)
    dp = container.get(keys.PARSER_DELEGATING)
    registered = set(type(p).__module__.split(".")[1] for p in dp.parsers)
    missing = EXPECTED_PARSERS - registered
    extra = registered - EXPECTED_PARSERS
    assert not missing, f"Parsers missing from DelegatingParser: {missing}"
    assert not extra, f"Unexpected parsers in DelegatingParser: {extra}"


def test_delegating_has_no_duplicates(stub_config):
    """Each parser appears exactly once in the DelegatingParser list."""
    container = load_container(stub_config)
    dp = container.get(keys.PARSER_DELEGATING)
    modules = [type(p).__module__ for p in dp.parsers]
    assert len(modules) == len(set(modules)), f"Duplicate parsers detected: {modules}"


def test_message_renderer_resolves(stub_config):
    """telega_message_renderer resolves to a MessageRenderer."""
    container = load_container(stub_config)
    renderer = container.get(keys.TELEGA_MESSAGE_RENDERER)
    assert isinstance(renderer, MessageRenderer)


def test_all_parser_keys_resolve(stub_config):
    """Every expected parser key resolves without error."""
    container = load_container(stub_config)
    for name in sorted(EXPECTED_PARSERS):
        key = keys.PARSER_TEMPLATE.format(name)
        service = container.get(key)
        assert service is not None, f"Service {key!r} resolved to None"


def test_delegating_parser_is_singleton(stub_config):
    """Repeated get() calls return the same DelegatingParser instance (lazy singleton)."""
    container = load_container(stub_config)
    dp1 = container.get(keys.PARSER_DELEGATING)
    dp2 = container.get(keys.PARSER_DELEGATING)
    assert dp1 is dp2
