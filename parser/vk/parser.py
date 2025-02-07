import re

import requests

from core import (
    Parser as BaseParser,
    Video,
    ParseError,
    Link,
    Content,
    HTMLMetaExtractor,
)


class Parser(BaseParser):
    VK_URL_REGEX = re.compile(r'https?://vk\.com/clip-?(\d+)_(\d+)')
    OK_URL_REGEX = re.compile(r"https?://ok\.ru/clip\?owner_id=(-?\d+)&clip_id=(\d+)")

    def __init__(self, thumbnail_url: str, user_agent: str):
        self.thumbnail_url = thumbnail_url
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        return any(pattern.match(url) for pattern in [
            self.VK_URL_REGEX,
            self.OK_URL_REGEX,
        ])

    def parse(self, url: str) -> Content:
        if not self.supports(url):
            raise ParseError('Unsupported url')

        response = requests.get(url, headers={'User-Agent': self.user_agent})
        if response.status_code != 200:
            raise ParseError('Unhandled response error')

        meta = HTMLMetaExtractor(response.text).extract()
        if 'og:video' not in meta:
            raise ParseError('Failed to retrieve video resource')

        if self.VK_URL_REGEX.match(url):
            backlink_url = meta.get('og:url')
        else:
            backlink_url = url

        return Content(
            backlink=Link(backlink_url),
            media=[
                Video(
                    resource_url=meta.get('og:video'),
                    mime_type='video/mp4',
                    thumbnail_url=self.thumbnail_url,
                )
            ],
        )
