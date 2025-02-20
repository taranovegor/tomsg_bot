import re

from pytubefix import YouTube

from core import (
    Parser as BaseParser,
    InvalidUrlError,
    ParseError,
    Link,
    Content,
)
from core.parser.entity import Video


class Parser(BaseParser):
    """A parser to extract video details from YouTube Shorts."""

    URL_REGEX = re.compile(
        r"https?://(?:www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]+"
    )

    def supports(self, url: str) -> bool:
        """Check if the given URL matches YouTube Shorts format."""
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Content:
        """Extract video details from YouTube Shorts."""
        if not self.supports(url):
            raise InvalidUrlError()

        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        if not stream:
            raise ParseError("Unable to retrieve video stream")

        return Content(
            backlink=Link(
                f"https://www.youtube.com/shorts/{yt.video_id}",
                yt.title,
            ),
            media=[
                Video(
                    resource_url=stream.url,
                    mime_type=stream.mime_type,
                    thumbnail_url=yt.thumbnail_url,
                ),
            ],
        )
