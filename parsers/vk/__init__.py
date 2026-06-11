from .parser import Parser as _VkParser
from parsers.registry import register, build_user_agent


@register("vk")
def create_parser(container):
    return _VkParser(
        container.config.vk.thumbnail_url,
        build_user_agent("TelegramBot (like TwitterBot)"),
        timeout=container.config.parser_http_timeout,
    )


Parser = _VkParser
__all__ = ["Parser"]
