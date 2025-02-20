import re
from datetime import datetime

import requests

from core import (
    Parser as BaseParser,
    InvalidUrlError,
    ParseError,
    Link,
    Content,
)


class Parser(BaseParser):
    """A parser to extract comment details from YouTube video comments."""

    URL_REGEX = re.compile(
        r"https?://(?:www\.)?(youtu.be|youtube\.com)/watch\?"
        r"(?:[^#]*&)?v=(?P<video_id>[a-zA-Z0-9_-]+)"
        r"(?:[^#]*&)?lc=(?P<comment_id>[a-zA-Z0-9_-]+)"
    )

    def __init__(self, api_key: str, user_agent: str):
        """Initialize parser with API key and user agent."""
        self.api_key = api_key
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        """Check if the given URL matches YouTube comment format."""
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Content:
        """Extract comment details from YouTube using API."""
        if not self.supports(url):
            raise InvalidUrlError()

        matches = self.URL_REGEX.search(url)
        comment_id = matches.group("comment_id")

        response = requests.get(
            f"https://youtube.googleapis.com/youtube/v3/comments"
            f"?id={comment_id}"
            f"&part=snippet"
            f"&key={self.api_key}",
            headers={"User-Agent": self.user_agent},
        )
        if response.status_code != 200:
            raise ParseError(
                f"Error fetching comment data: HTTP {response.status_code}."
            )

        items = response.json().get("items", [])
        if not items:
            raise ParseError("No comment data found in response.")

        item = items[0]["snippet"]

        video_id = matches.group("video_id")
        backlink = Link(f"https://youtu.be/watch?v={video_id}&lc={comment_id}")
        author = Link(item["authorChannelUrl"], item["authorDisplayName"])
        metrics = [f"👍 {item['likeCount']}"] if "likeCount" in item else None

        return Content(
            backlink=backlink,
            text=item["textDisplay"],
            author=author,
            metrics=metrics,
            created_at=datetime.fromisoformat(item["publishedAt"]),
        )
