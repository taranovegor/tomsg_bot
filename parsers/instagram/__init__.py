from parsers.registry import register

from .parser import Parser as _InstagramParser


@register("instagram")
def create_parser(container):
    return _InstagramParser(
        timeout=container.config.parser_http_timeout,
        proxy=container.config.instagram.proxy,
    )


Parser = _InstagramParser
__all__ = ["Parser"]
