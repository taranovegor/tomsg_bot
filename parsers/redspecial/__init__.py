from .parser import Parser as _RedspecialParser
from parsers.registry import register, build_user_agent


@register("redspecial")
def create_parser(container):
    return _RedspecialParser(
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _RedspecialParser
__all__ = ["Parser"]
