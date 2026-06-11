from .parser import Parser as _HabrParser
from parsers.registry import register, build_user_agent


@register("habr")
def create_parser(container):
    return _HabrParser(
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _HabrParser
__all__ = ["Parser"]
