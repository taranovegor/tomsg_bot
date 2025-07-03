import re

import requests

from core import (
    Parser as BaseParser,
    Video,
    Photo,
    Content,
    InvalidUrlError,
    ParseError,
    Link,
)
from .cipher import Cipher


class Parser(BaseParser):
    URL_REGEX = re.compile(r'^https?://(?:www\.)?instagram\.com/(p|reels?)/[\w-]+/?.*')

    def __init__(self, parser_url: str, user_agent: str, cipher: Cipher):
        self.parser_url = parser_url
        self.user_agent = user_agent
        self.cipher = cipher

    def supports(self, url: str) -> bool:
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Content:
        match = self.URL_REGEX.search(url)
        if not match:
            raise InvalidUrlError()

        response = requests.get(self.parser_url, headers={
            'User-Agent': self.user_agent,
            'Url': self.cipher.encrypt(url),
        })
        if response.status_code != 200:
            raise ParseError('Unhandled response error')

        try:
            data = response.json()

            media = []

            for item in data.get('video', []):
                media.append(
                    Video(
                        resource_url=item["video"],
                        mime_type="video/mp4",
                        thumbnail_url=item["thumbnail"],
                    )
                )

            for item in data.get('image', []):
                media.append(
                    Photo(resource_url=item)
                )

            if len(media) == 0:
                raise ParseError('Expected at least one video or image in media data, but none found')

        except (KeyError, IndexError, AttributeError) as e:
            raise ParseError(f'Failed to parse response: {str(e)}')

        return Content(
            backlink=Link(url),
            media=media,
        )
