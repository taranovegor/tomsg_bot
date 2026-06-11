from .parser import Parser as _TumblrParser
from parsers.registry import register, build_user_agent


@register("tumblr")
def create_parser(container):
    return _TumblrParser(
        container.config.tumblr.api_key,
        build_user_agent("TelegramBot (like TwitterBot)"),
        timeout=container.config.parser_http_timeout,
    )


Parser = _TumblrParser
__all__ = ["Parser"]
