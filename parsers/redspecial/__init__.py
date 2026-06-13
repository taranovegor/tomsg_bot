from parsers.registry import build_user_agent, register

from .parser import Parser as _RedspecialParser


@register("redspecial")
def create_parser(container):
    return _RedspecialParser(
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _RedspecialParser
__all__ = ["Parser"]
