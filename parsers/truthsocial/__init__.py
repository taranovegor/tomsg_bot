from .parser import Parser as _TruthSocialParser
from parsers.registry import register


@register("truthsocial")
def create_parser(container):
    return _TruthSocialParser(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 tomsg_bot",
        timeout=container.config.parser_http_timeout,
    )


Parser = _TruthSocialParser
__all__ = ["Parser"]
