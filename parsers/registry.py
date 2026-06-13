import logging
import os
from collections.abc import Callable
from typing import Any

_parser_factories: dict[str, Callable[[Any], object]] = {}


def register(name: str):
    """Decorator to register a parser factory function.

    The decorated function receives a container (or config-like object)
    and must return a Parser instance.

    Usage:
        @register("twitter")
        def _(container):
            return TwitterParser(...)
    """

    def decorator(fn):
        if name in _parser_factories:
            logging.warning("Parser factory %r is already registered. Overwriting.", name)
        _parser_factories[name] = fn
        return fn

    return decorator


def get_factories() -> dict[str, Callable[[Any], object]]:
    """Return all registered parser factories (copy to prevent mutation)."""
    return dict(_parser_factories)


def build_user_agent(suffix=""):
    """Build a standard user-agent string from app metadata, with optional suffix."""
    from shared.info import name, version

    base = f"{os.name}:{name()}:{version()}"
    return f"{base} {suffix}".strip() if suffix else base
