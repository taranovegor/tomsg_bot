from .parser import Parser as _TwitterParser
from parsers.registry import register, build_user_agent


@register("twitter")
def create_parser(container):
    return _TwitterParser(
        build_user_agent("TelegramBot (like TwitterBot)"),
        timeout=container.config.parser_http_timeout,
    )


Parser = _TwitterParser
__all__ = ["Parser"]
