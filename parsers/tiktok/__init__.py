from .parser import Parser as _TikTokParser
from parsers.registry import register, build_user_agent


@register("tiktok")
def create_parser(container):
    config = container.config.tiktok
    return _TikTokParser(
        config.video_resource_url,
        config.thumbnail_resource_url,
        build_user_agent(),
        timeout=container.config.parser_http_timeout,
    )


Parser = _TikTokParser
__all__ = ["Parser"]
