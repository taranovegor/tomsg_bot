import re

import requests

from core import (
    Parser as BaseParser,
    Video,
    InvalidUrlError,
    ParseError,
    Link,
    Content,
    HTMLMetaExtractor,
)


class Parser(BaseParser):
    VK_URL_REGEX = re.compile(
        r"https?://vk\.com/"
        r"(?:clips/[^?]+?\?z=|clips/)?"
        r"clip(?P<owner_id>-?\d+)_(?P<clip_id>\d+)"
    )
    OK_URL_REGEX = re.compile(
        r"https?://ok\.ru/clip"
        r"\?owner_id=(?P<owner_id>-?\d+)"
        r"&clip_id=(?P<clip_id>\d+)"
    )

    def __init__(self, thumbnail_url: str, user_agent: str):
        self.thumbnail_url = thumbnail_url
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        return any(
            pattern.match(url)
            for pattern in [
                self.VK_URL_REGEX,
                self.OK_URL_REGEX,
            ]
        )

    def parse(self, url: str) -> Content:
        if not self.supports(url):
            raise InvalidUrlError()

        if self.VK_URL_REGEX.match(url):
            matches = self.VK_URL_REGEX.search(url)
            url = (
                f"https://vk.com"
                f"/clip{matches.group('owner_id')}"
                f"_{matches.group('clip_id')}"
            )

        response = requests.get(url, headers={"User-Agent": self.user_agent})
        if response.status_code != 200:
            raise ParseError(
                "Failed to fetch the page. HTTP status: %s",
                response.status_code,
            )

        meta = HTMLMetaExtractor(response.text).extract()
        if "og:video" not in meta:
            raise ParseError(
                "Missing 'og:video' metadata, unable to retrieve video URL"
            )

        if self.VK_URL_REGEX.match(url):
            backlink_url = meta.get("og:url")
        else:
            backlink_url = url

        return Content(
            backlink=Link(backlink_url),
            media=[
                Video(
                    resource_url=meta.get("og:video"),
                    mime_type="video/mp4",
                    thumbnail_url=self.thumbnail_url,
                )
            ],
        )
