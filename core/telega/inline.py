import re
from uuid import uuid4

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

    def create(self, content: Content) -> list[InlineQueryResult]:
        """Creates inline query results for the provided content."""
        text = self._generate_text_description(content)
        backlink = self._format_link_as_html(content.backlink)
        results = []

        if text:
            results.append(self._generate_message_result(text, backlink))

        if not len(text) > 1024:
            results.extend(self._generate_media_results(content.media, text, backlink))

        return results

    def _generate_message_result(self, text: str, backlink: str) -> InlineQueryResult:
        """Generates a message result (inline article) with text and a backlink."""
        return InlineQueryResultArticle(
            id=self._generate_unique_id(),
            title="➡️ Отправить как сообщение",
            description=re.sub(r"<.*?>", "", text),
            input_message_content=InputTextMessageContent(
                message_text=self._combine_text_with_link(text, "📄", backlink),
                parse_mode=ParseMode.HTML,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            ),
        )

    def _generate_media_results(
        self, media_list, text: str, backlink: str
    ) -> list[InlineQueryResult]:
        """Generates media results (photos, videos, GIFs) for the given media list."""
        media_results = []
        emoji_map = {"photo": "🖼", "video": "📺", "gif": "🎞️"}

        for media in media_list:
            media_type = media.type()
            if media_type in emoji_map:
                media_results.append(
                    self._create_inline_media_result(
                        media, text, backlink, emoji_map[media_type]
                    )
                )

        return media_results

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
            "description": text,
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
