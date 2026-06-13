from parsers.registry import build_user_agent, register

from .parser import Cipher as _Cipher
from .parser import Parser as _InstagramParser


@register("instagram")
def create_parser(container):
    config = container.config.instagram
    cipher = _Cipher(config.encryption_key)
    return _InstagramParser(
        config.parser_url,
        build_user_agent("TelegramBot (like TwitterBot)"),
        cipher,
        timeout=container.config.parser_http_timeout,
    )


Parser = _InstagramParser
Cipher = _Cipher
__all__ = ["Parser", "Cipher"]
