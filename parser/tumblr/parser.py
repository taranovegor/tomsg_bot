import re
from datetime import datetime, timezone

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
    """Parser for Tumblr URLs to extract post information."""

    URL_REGEX = re.compile(
        r"https?://(?:(?P<blog_domain>[^.]+)\.tumblr\.com/post/|(?:www\.)?tumblr\.com/(?:blog/view/)?(?P<blog_path>[^/]+)/)(?P<post_id>\d+)"
    )

    VIDEO_SOURCE_PATTERN = re.compile(r'<source\s+src="([^"]+)"\s+type="([^"]+)"')
    VIDEO_POSTER_PATTERN = re.compile(r'<video[^>]+poster="([^"]+)"')
    IMG_PATTERN = re.compile(r'<img[^>]+src="([^"]+)"')
    HTML_TAGS_PATTERN = re.compile(r"<[^>]+>")

    MIME_GIF = "image/gif"
    MIME_MP4 = "video/mp4"

    def __init__(self, api_key: str, user_agent: str):
        """Initializes the parser with Tumblr API key and user agent."""
        self.api_key = api_key
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        """Checks if the URL is supported by this parser."""
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Entity:
        """Parses the provided Tumblr URL and returns an Entity representing the post."""
        match = self.URL_REGEX.search(url)
        if not match:
            raise InvalidUrlError()

        # Support both URL formats: domain.tumblr.com/post/id and tumblr.com/blog/...
        blog_name = match.group("blog_domain") or match.group("blog_path")
        post_id = match.group("post_id")

        response = requests.get(
            f"https://api.tumblr.com/v2/blog/{blog_name}.tumblr.com/posts",
            params={"id": post_id, "api_key": self.api_key},
            headers={"User-Agent": self.user_agent},
        )

        if response.status_code != 200:
            raise ParseError("Unhandled response error")

        data = response.json()
        if not data.get("response") or not data["response"].get("posts"):
            raise ParseError("No post found")

        post = data["response"]["posts"][0]

        author = Link(
            f"https://www.tumblr.com/{post['blog_name']}",
            post.get("blog", {}).get("title", post["blog_name"]),
        )

        content = self._extract_content(post)
        created_at = self._parse_date(post["date"])
        media = self._extract_media(post)

        metrics = [f"💬 {self.format_counter(post.get('notes', 0))}"]
        backlink = Link(post["post_url"])

        return Content(
            author=author,
            created_at=created_at,
            metrics=metrics,
            text=content,
            backlink=backlink,
            media=media,
        )

    @staticmethod
    def _extract_content(post: dict) -> str:
        """Extracts text content from post body."""
        body = post.get("body", "")
        content = Parser.HTML_TAGS_PATTERN.sub("", body)
        return content.strip()

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parses Tumblr date format to datetime with UTC timezone."""
        cleaned = date_str.replace(" GMT", "").strip()
        return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

    def _extract_media(self, post: dict) -> list:
        """Extracts media from post photos, videos, or HTML body."""
        media = []

        if post.get("photos"):
            media.extend(self._extract_photos_from_field(post["photos"]))

        if post.get("video_url"):
            media.append(Video(
                resource_url=post["video_url"],
                mime_type=self.MIME_MP4,
                thumbnail_url=post.get("thumbnail_url"),
            ))

        if not media and post.get("body"):
            body = post["body"]
            media.extend(self._extract_videos_from_html(body))
            if not media:
                media.extend(self._extract_images_from_html(body))

        return media

    def _extract_photos_from_field(self, photos: list) -> list:
        """Extracts Photo/GIF objects from photos field."""
        media = []
        for photo in photos:
            original_size = photo.get("original_size", {})
            if url := original_size.get("url"):
                thumb_url = photo.get("alt_sizes", [{}])[0].get("url")
                media.append(self._create_media_object(url, thumb_url))
        return media

    def _extract_videos_from_html(self, html: str) -> list:
        """Extracts Video objects from HTML <source> tags."""
        media = []
        video_matches = self.VIDEO_SOURCE_PATTERN.findall(html)
        if not video_matches:
            return media

        poster_match = self.VIDEO_POSTER_PATTERN.search(html)
        poster_url = poster_match.group(1) if poster_match else None

        for video_url, mime_type in video_matches:
            media.append(Video(
                resource_url=video_url,
                mime_type=mime_type,
                thumbnail_url=poster_url,
                # todo: possible to set height, width
            ))
        return media

    def _extract_images_from_html(self, html: str) -> list:
        """Extracts Photo/GIF objects from HTML <img> tags."""
        media = []
        img_urls = self.IMG_PATTERN.findall(html)

        seen = set()
        for img_url in img_urls:
            if img_url not in seen:
                seen.add(img_url)
                media.append(self._create_media_object(img_url, img_url))
        return media

    def _create_media_object(self, resource_url: str, thumbnail_url: str) -> Photo | Video:
        """Creates appropriate media object (Photo, GIF, or Video) based on URL."""
        if resource_url.lower().endswith('.gif'):
            return Video(
                resource_url=resource_url,
                mime_type=self.MIME_GIF,
                thumbnail_url=thumbnail_url,
                # todo: possible to set height, width
            )
        return Photo(resource_url=resource_url, thumbnail_url=thumbnail_url)

    @staticmethod
    def format_counter(number: int) -> str:
        """Formats a number into a human-readable counter (e.g., 1K, 1M)."""
        if number >= 1_000_000:
            return f"{number / 1_000_000:.0f}M"
        if number >= 1_000:
            return f"{number / 1_000:.0f}K"
        return str(number)
