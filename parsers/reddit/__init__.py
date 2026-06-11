from .parser import Parser as _RedditParser
from .html_adapter import HTMLNodeAdapter
from parsers.registry import register, build_user_agent


@register("reddit")
def create_parser(container):
    config = container.config.reddit
    return _RedditParser(
        config.client_id,
        config.client_secret,
        build_user_agent(f"(by /u/{config.app_owner_username})"),
        timeout=container.config.parser_http_timeout,
    )


Parser = _RedditParser
__all__ = ["Parser", "HTMLNodeAdapter"]
