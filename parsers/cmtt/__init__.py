from parsers.registry import build_user_agent, register

from .parser import Parser as _CmttParser


@register("cmtt")
def create_parser(container):
    return _CmttParser(
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _CmttParser
__all__ = ["Parser"]
