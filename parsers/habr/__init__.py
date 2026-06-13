from parsers.registry import build_user_agent, register

from .parser import Parser as _HabrParser


@register("habr")
def create_parser(container):
    return _HabrParser(
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _HabrParser
__all__ = ["Parser"]
