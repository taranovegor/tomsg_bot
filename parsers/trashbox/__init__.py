from parsers.registry import build_user_agent, register

from .parser import Parser as _TrashboxParser


@register("trashbox")
def create_parser(container):
    return _TrashboxParser(
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _TrashboxParser
__all__ = ["Parser"]
