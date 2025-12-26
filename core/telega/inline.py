import re
from uuid import uuid4
import logging
import aiohttp
from telegram import (
    InlineQueryResult,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
    InlineQueryResultVideo,
    InlineQueryResultPhoto,
    InlineQueryResultGif,
)
from telegram.constants import ParseMode

from core import Content, Link, Photo, Video, GIF


class InlineResultsFactory:
    """Factory for generating inline query results from content."""

    MAX_MEDIA_SIZE = 20 * 1024 * 1024  # 20 MB

    def __init__(self, user_agent: str):
        """Initializes the parser with a user agent for making requests."""
        self.user_agent = user_agent

    async def create(self, content: Content) -> list[InlineQueryResult]:
        """Creates inline query results for the provided content (async to allow HEAD checks)."""
        text = self._generate_text_description(content)
        backlink = self._format_link_as_html(content.backlink)
        results = []

        if text:
            results.append(self._generate_message_result(text, backlink))

        if content.media and not len(text) > 1024:
            results.extend(await self._generate_media_results(content.media, text, backlink))

        return results

    def _generate_message_result(self, text: str, backlink: str) -> InlineQueryResult:
        """Generates a message result (inline article) with text and a backlink."""
        return InlineQueryResultArticle(
            id=self._generate_unique_id(),
            title="➡️ Отправить как сообщение",
            description=self._strip_tags(text),
            input_message_content=InputTextMessageContent(
                message_text=self._combine_text_with_link(text, "📄", backlink),
                parse_mode=ParseMode.HTML,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            ),
        )

    async def _generate_media_results(
        self, media_list: list, text: str, backlink: str
    ) -> list[InlineQueryResult]:
        """Generates media results (photos, videos, GIFs) for the given media list."""
        media_results = []
        emoji_map = {"photo": "🖼", "video": "📺", "gif": "🎞️"}

        for media in media_list:
            media_type = media.type()
            if media_type == "video":
                try:
                    too_large = await self._is_media_too_large(media.resource_url)
                except Exception:
                    logging.exception("Failed to check video size for %s; including by default", media.resource_url)
                    too_large = False

                if too_large:
                    logging.info("Skipping video (too large): %s", media.resource_url)
                    continue

            if media_type in emoji_map:
                media_results.append(
                    self._create_inline_media_result(
                        media, text, backlink, emoji_map[media_type]
                    )
                )

        return media_results

    async def _is_media_too_large(self, url: str) -> bool:
        """Perform a HEAD request to determine Content-Length. Return True if > MAX_VIDEO_SIZE."""
        timeout = aiohttp.ClientTimeout(total=5)
        headers = {"User-Agent": self.user_agent}
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(url, headers=headers, allow_redirects=True) as resp:
                    # Some servers may not support HEAD properly; if 405 try GET with range
                    if resp.status == 405:
                        async with session.get(url, headers={**headers, "Range": "bytes=0-0"}, allow_redirects=True) as get_resp:
                            cl = get_resp.headers.get("Content-Length")
                    else:
                        cl = resp.headers.get("Content-Length")
                    if cl is None:
                        return False
                    try:
                        size = int(cl)
                        return size > self.MAX_MEDIA_SIZE
                    except Exception:
                        logging.exception("Invalid Content-Length header for %s: %s", url, cl)
                        return False
        except Exception:
            logging.exception("Error checking Content-Length for %s", url)
            return False

    def _create_inline_media_result(
        self, media: Video | Photo | GIF, text: str, backlink: str, emoji: str
    ) -> InlineQueryResult:
        """Generates inline media results for a specific media type (photo, video, or GIF)."""
        media_name = {"photo": "фото", "video": "видео", "gif": "GIF"}

        common_params = {
            "id": self._generate_unique_id(),
            "title": f"➡️ Отправить {media_name[media.type()]}",
            "caption": self._combine_text_with_link(text, emoji, backlink),
            "parse_mode": ParseMode.HTML,
            "description": self._strip_tags(text),
        }

        match media.type():
            case "photo":
                return InlineQueryResultPhoto(
                    photo_url=media.resource_url,
                    thumbnail_url=media.thumbnail_url or media.resource_url,
                    **common_params,
                )
            case "video":
                return InlineQueryResultVideo(
                    video_url=media.resource_url,
                    mime_type=media.mime_type,
                    thumbnail_url=media.thumbnail_url,
                    **common_params,
                )
            case "gif":
                return InlineQueryResultGif(
                    gif_url=media.resource_url,
                    thumbnail_url=media.thumbnail_url,
                    **common_params,
                )

    @staticmethod
    def _generate_text_description(content: Content) -> str:
        """Generates a text description for the content (including author, date, text, and metrics)."""
        body = ""
        if content.author:
            body += "💁"
            body += InlineResultsFactory._format_link_as_html(content.author)
        if content.created_at:
            body += ", " if body else ""
            body += content.created_at.strftime("%d.%m.%y %H:%M %Z")
        if content.author or content.created_at:
            body += "\n"
        if content.text:
            body += f"{content.text}\n\n"
        elif content.author or content.created_at:
            body += "\n"
        if content.metrics:
            body += "  ".join(content.metrics)
        return body.strip()

    @staticmethod
    def _strip_tags(html: str) -> str:
        return re.sub(r"<.*?>", "", html)

    @staticmethod
    def _format_link_as_html(link: Link) -> str:
        """Formats a link as an HTML anchor tag."""
        return (
            f'<a href="{link.url}">{link.text or link.url}</a>'
            if link.url
            else str(link.text)
        )

    @staticmethod
    def _combine_text_with_link(body: str, emoji: str, backlink: str) -> str:
        """Combines text with a backlink and emoji."""
        return f"{body}\n\n{emoji}{backlink}".strip()

    @staticmethod
    def _generate_unique_id() -> str:
        """Generates a unique ID for the inline query result."""
        return str(uuid4())
