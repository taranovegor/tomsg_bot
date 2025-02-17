import re
from datetime import datetime

import requests

from core import (
    Parser as BaseParser,
    Entity,
    Content,
    Video,
    InvalidUrlError,
    ParseError,
    Link,
    Photo,
)


class Parser(BaseParser):
    """Parser for Twitter URLs to extract tweet information."""

    URL_REGEX = re.compile(
            r"https?://(?:x\.com|twitter\.com|fxtwitter.com|fixupx.com)/"
        r"(?P<username>[^/]+)/status/(?P<status_id>\d+)"
    )

    def __init__(self, user_agent: str):
        """Initializes the parser with a user agent for making requests."""
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        """Checks if the URL is supported by this parser."""
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Entity:
        """Parses the provided Twitter URL and returns an Entity representing the tweet."""
        match = self.URL_REGEX.search(url)
        if not match:
            raise InvalidUrlError()

        status_id = match.group("status_id")

        response = requests.get(
            f"https://api.fxtwitter.com/status/{status_id}",
            headers={"User-Agent": self.user_agent},
        )
        if response.status_code != 200:
            raise ParseError("Unhandled response error")

        json = response.json()
        if json["code"] != 200:
            raise ParseError("Unhandled response error")

        tweet = json["tweet"]

        # Create author link and clean up author name
        author = Link(
            f"https://x.com/{tweet['author']['screen_name']}",
            re.sub(r"\s*\(@[^)]+\)", "", tweet["author"]["name"]),
        )

        content = tweet["text"] if "text" in tweet else ""
        metrics = [
            f"💬 {self.format_counter(tweet['replies'])}",
            f"🔁 {self.format_counter(tweet['retweets'])}",
            f"❤️ {self.format_counter(tweet['likes'])}",
            f"📊 {self.format_counter(tweet['views'])}",
        ]

        created_at = datetime.strptime(
            tweet["created_at"],
            "%a %b %d %H:%M:%S %z %Y",
        )

        backlink = Link(
            f"https://x.com/{tweet['author']['screen_name']}/status/{status_id}"
        )

        media = []
        if "media" in tweet:
            for item in tweet["media"]["all"]:
                match item["type"]:
                    case "photo":
                        media.append(Photo(resource_url=item["url"]))
                    case "video" | "gif":
                        media.append(
                            Video(
                                resource_url=item["url"],
                                mime_type="video/mp4",
                                thumbnail_url=item["thumbnail_url"],
                            )
                        )

        return Content(
            author=author,
            created_at=created_at,
            metrics=metrics,
            text=content,
            backlink=backlink,
            media=media,
        )

    @staticmethod
    def format_counter(number):
        """Formats a number into a human-readable counter (e.g., 1K, 1M)."""
        if number >= 1_000_000:
            return f"{number / 1_000_000:.0f}M"
        if number >= 1_000:
            return f"{number / 1_000:.0f}K"
        return str(number)
