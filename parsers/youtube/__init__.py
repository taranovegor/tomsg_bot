from .parser import Parser as _YoutubeParser
from parsers.registry import register, build_user_agent


@register("youtube")
def create_parser(container):
    return _YoutubeParser(
        container.config.youtube.api_key,
        build_user_agent("TelegramBot (like TwitterBot)"),
        timeout=container.config.parser_http_timeout,
    )


Parser = _YoutubeParser
__all__ = ["Parser"]
