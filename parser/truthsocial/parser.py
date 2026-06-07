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
    """Parser for Truth Social URLs to extract status information."""

    URL_REGEX = re.compile(
        r"https?://truthsocial\.com/"
        r"@(?P<username>[^/]+)/(?:posts/)?(?P<status_id>\d+)"
    )

    def __init__(self, user_agent: str, timeout: int = 30):
        """Initializes the parser with a user agent for making requests."""
        self.user_agent = user_agent
        self.timeout = timeout

    def supports(self, url: str) -> bool:
        """Checks if the URL is supported by this parser."""
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Entity:
        """Parses the provided Truth Social URL and returns an Entity representing the status."""
        match = self.URL_REGEX.search(url)
        if not match:
            raise InvalidUrlError()

        status_id = match.group("status_id")

        response = requests.get(
            f"https://truthsocial.com/api/v1/statuses/{status_id}",
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise ParseError("Unhandled response error")

        status = response.json()

        account = status["account"]
        author = Link(
            account["url"],
            account["display_name"] or account["username"],
        )

        # Remove HTML tags from content
        content = re.sub(r"<[^>]+>", "", status["content"])

        metrics = [
            f"💬 {self.format_counter(status['replies_count'])}",
            f"🔁 {self.format_counter(status['reblogs_count'])}",
            f"❤️ {self.format_counter(status['favourites_count'])}",
        ]

        created_at = datetime.fromisoformat(status["created_at"].replace("Z", "+00:00"))

        backlink = Link(status["url"])

        media = []
        for attachment in status.get("media_attachments", []):
            match attachment["type"]:
                case "image":
                    media.append(Photo(
                        resource_url=attachment["url"],
                        thumbnail_url=attachment.get("preview_url"),
                    ))
                case "video" | "gifv":
                    media.append(
                        Video(
                            resource_url=attachment["url"],
                            mime_type="video/mp4",
                            thumbnail_url=attachment.get("preview_url"),
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
