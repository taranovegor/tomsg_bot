import logging
import re
from datetime import UTC, datetime

from yt_dlp import YoutubeDL

from core import (
    Content,
    InvalidUrlError,
    Link,
    ParseError,
    Video,
)
from core import (
    Parser as BaseParser,
)

# Prefer a single progressive file (video + audio) so no muxing is needed.
_FORMAT = "best[vcodec!=none][acodec!=none]/best"


class _YtDlpLogger:
    """Route yt-dlp output to logging and remember errors for the ParseError message."""

    def __init__(self):
        self.errors: list[str] = []

    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        logging.debug("yt-dlp: %s", msg)

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        logging.debug("yt-dlp: %s", msg)


class Parser(BaseParser):
    """Instagram parser backed by yt-dlp. Supports video posts and reels only."""

    URL_REGEX = re.compile(r"^https?://(?:www\.)?instagram\.com/(p|reels?|share)/[\w-]+/?.*")

    def __init__(self, timeout: int = 30, proxy: str | None = None):
        self.proxy = proxy
        self.timeout = timeout

    def supports(self, url: str) -> bool:
        return bool(self.URL_REGEX.match(url))

    def parse(self, url: str) -> Content:
        if not self.URL_REGEX.match(url):
            raise InvalidUrlError()

        logger = _YtDlpLogger()
        options = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "skip_download": True,
            # Carousels: skip items without video instead of failing the whole post.
            "ignoreerrors": True,
            "socket_timeout": self.timeout,
            "format": _FORMAT,
            "logger": logger,
        }
        if self.proxy:
            options["proxy"] = self.proxy

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        entries = [e for e in ((info or {}).get("entries") or [info]) if e]
        media = [self._video(e) for e in entries if e.get("url")]
        if not media:
            raise ParseError(self._failure_reason(logger.errors))

        # Carousel: post-level fields win, missing ones fall back to the first item.
        meta = {**entries[0], **{k: v for k, v in info.items() if v is not None}}

        return Content(
            backlink=Link(url),
            text=meta.get("description") or None,
            author=self._author(meta),
            metrics=self._metrics(meta),
            created_at=self._created_at(meta),
            media=media,
        )

    @staticmethod
    def _failure_reason(errors: list[str]) -> str:
        no_video = ("There is no video in this post", "No video formats found")
        if errors and all(any(marker in e for marker in no_video) for e in errors):
            return "Instagram post has no video; photo posts are not supported"
        return f"yt-dlp failed to extract media: {errors[-1] if errors else 'no data'}"

    @staticmethod
    def _video(entry: dict) -> Video:
        return Video(
            resource_url=entry["url"],
            mime_type="video/mp4",
            thumbnail_url=entry.get("thumbnail"),
        )

    @staticmethod
    def _author(meta: dict) -> Link | None:
        username = meta.get("channel")
        if not username:
            return None
        return Link(f"https://www.instagram.com/{username}/", meta.get("uploader") or username)

    @classmethod
    def _metrics(cls, meta: dict) -> list[str] | None:
        metrics = []
        if meta.get("comment_count") is not None:
            metrics.append(f"💬 {cls.format_counter(meta['comment_count'])}")
        if meta.get("like_count") is not None:
            metrics.append(f"❤️ {cls.format_counter(meta['like_count'])}")
        return metrics or None

    @staticmethod
    def _created_at(meta: dict) -> datetime | None:
        timestamp = meta.get("timestamp")
        return datetime.fromtimestamp(timestamp, UTC) if timestamp else None

    @staticmethod
    def format_counter(number: int) -> str:
        if number >= 1_000_000:
            return f"{number / 1_000_000:.0f}M"
        if number >= 1_000:
            return f"{number / 1_000:.0f}K"
        return str(number)
