from .parser import Parser as _CmttParser
from parsers.registry import register, build_user_agent


@register("cmtt")
def create_parser(container):
    return _CmttParser(
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _CmttParser
__all__ = ["Parser"]
