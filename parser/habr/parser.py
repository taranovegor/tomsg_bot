import re
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from core import (
    Parser as BaseParser,
    InvalidUrlError,
    ParseError,
    Content,
    Link,
)
from parser.habr.html_processor import HTMLProcessor


class Parser(BaseParser):
    """Parser for extracting comments from Habr articles."""

    URL_REGEX = re.compile(r"https?://habr\.com/[^/]+/[^/]+/(\d+)/#comment_(\d+)")

    def __init__(self, user_agent: str):
        """Initialize parser with a custom User-Agent."""
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        """Check if the given URL matches the expected pattern."""
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Content:
        """Extract comment data from a given Habr article URL."""
        match = self.URL_REGEX.search(url)
        if not match:
            raise InvalidUrlError()

        article_id, comment_id = match.groups()
        with ThreadPoolExecutor() as executor:
            article_future = executor.submit(
                self._fetch,
                f"https://habr.com/kek/v2/articles/{article_id}/",
            )
            comments_future = executor.submit(
                self._fetch,
                f"https://habr.com/kek/v2/articles/{article_id}/comments/split/guest/",
            )

            article = article_future.result()
            comments = comments_future.result().get("commentRefs", {})

        if comment_id not in comments:
            raise ParseError("Specified comment does not exist")

        comment = comments[comment_id]
        author = comment["author"]["alias"]

        return Content(
            author=Link(url=f"https://habr.com/ru/users/{author}/", text=author),
            created_at=datetime.fromisoformat(comment["timePublished"]),
            text=HTMLProcessor().process(comment["message"]),
            backlink=Link(
                f"https://habr.com/ru/articles/{article_id}/#comment_{comment_id}",
                article["titleHtml"],
            ),
        )

    def _fetch(self, url: str) -> dict:
        """Perform an HTTP GET request and return the JSON response."""
        response = requests.get(url, headers={"User-Agent": self.user_agent})
        if response.status_code == 200:
            return response.json()
        raise ParseError(f"Request failed with status code: {response.status_code}")
