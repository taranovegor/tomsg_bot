import re
from datetime import datetime
from urllib.parse import unquote

import requests

from core import (
    Parser as BaseParser,
    Entity,
    Content,
    Video,
    ParseError,
    Link,
    HTMLMetaExtractor,
)


class Parser(BaseParser):
    URL_REGEX = re.compile(r'https?://(?:x\.com|twitter\.com)/(?P<username>[^/]+)/status/(?P<status_id>\d+)')

    def __init__(self, video_resource_url: str, user_agent: str):
        self.video_resource_url = video_resource_url
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Entity:
        match = self.URL_REGEX.search(url)
        if not match:
            raise ParseError('Unsupported url')

        username = match.group('username')
        status_id = match.group('status_id')

        response = requests.get(
            self.video_resource_url.format(username, status_id),
            headers={'User-Agent': self.user_agent},
        )
        if response.status_code != 200:
            raise ParseError('Unhandled response error')

        meta = HTMLMetaExtractor(response.text).extract()

        author = Link(
            f'https://x.com/{meta.get('twitter:creator')}',
            re.sub(r'\s*\(@[^)]+\)', '', meta.get('twitter:title')),
        )
        content = meta.get('og:description').replace('<br>', '\n')
        backlink = Link(f'https://x.com/{username}/status/{status_id}', '')
        if 'article:published_time' in meta:
            created_at = datetime.fromisoformat(meta.get('article:published_time'))
        else:
            created_at = None

        media = []
        if 'og:video' in meta:
            media.append(Video(
                resource_url=unquote(meta.get('og:video')),
                mime_type=meta.get('og:video:type'),
                thumbnail_url=meta.get('og:image'),
            ))

        return Content(
            author=author,
            created_at=created_at,
            metrics=[],
            text=content,
            backlink=backlink,
            media=media,
        )
