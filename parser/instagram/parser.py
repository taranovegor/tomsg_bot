import re

import requests

from core import (
    Parser as BaseParser,
    Video,
    Content,
    InvalidUrlError,
    ParseError,
    Link,
    HTMLMetaExtractor,
)


class Parser(BaseParser):
    URL_REGEX = re.compile(r'^https?://(?:www\.)?instagram\.com/(?P<type>reels?)/(?P<id>[\w-]+)/?.*')

    def __init__(self, video_resource_url: str, video_storage_url: str, thumbnail_url: str, user_agent: str):
        self.video_resource_url = video_resource_url
        self.video_storage_url = video_storage_url
        self.thumbnail_url = thumbnail_url
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Content:
        match = self.URL_REGEX.search(url)
        if not match:
            raise InvalidUrlError()

        c_id = match.group('id')
        c_type = match.group('type')

        response = requests.get(self.video_resource_url.format(c_type, c_id), headers={'User-Agent': self.user_agent})
        if response.status_code != 200:
            raise ParseError('Unhandled response error')

        meta = HTMLMetaExtractor(response.text).extract()
        if 'og:video' not in meta:
            raise ParseError('Failed to retrieve video resource')

        return Content(
            backlink=Link(meta.get('og:url')),
            media=[
                Video(
                    resource_url=self.video_storage_url.format(meta.get('og:video')),
                    mime_type='video/mp4',
                    thumbnail_url=self.thumbnail_url,
                ),
            ]
        )
