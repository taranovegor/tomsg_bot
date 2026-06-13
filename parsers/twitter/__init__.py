from parsers.registry import build_user_agent, register

from .parser import Parser as _TwitterParser


@register("twitter")
def create_parser(container):
    return _TwitterParser(
        build_user_agent("TelegramBot (like TwitterBot)"),
        timeout=container.config.parser_http_timeout,
    )


Parser = _TwitterParser
__all__ = ["Parser"]
