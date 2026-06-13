"""
Tests for inline query handling.

thumbnail_url=None for Video/GIF caused Telegram API errors because
InlineQueryResultGif and InlineQueryResultVideo require a non-null thumbnail_url.
The fix adds a fallback to resource_url when thumbnail_url is absent.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_handler():
    from platforms.telegram.inline_query import InlineQueryHandler
    from platforms.telegram.renderer import MessageRenderer

    validator = MagicMock()
    validator.validate_size = AsyncMock(return_value=None)
    analytics = MagicMock()
    analytics.log = AsyncMock()

    return InlineQueryHandler(
        parser=MagicMock(),
        renderer=MessageRenderer(),
        file_validator=validator,
        analytics=analytics,
    )


def _make_inline_query(url: str, user_id: int = 7):
    iq = MagicMock()
    iq.query = url
    iq.from_user.id = user_id
    iq.answer = AsyncMock()
    return iq


class TestGifThumbnailFallback:
    @pytest.mark.asyncio
    async def test_gif_without_thumbnail_uses_resource_url(self):
        from telegram import InlineQueryResultGif

        from core.domain.entity import GIF, Content

        handler = _make_handler()
        content = Content(
            backlink=MagicMock(url="https://x.com/u/status/1"),
            media=[
                GIF(
                    resource_url="http://cdn.test/anim.gif",
                    mime_type="image/gif",
                    thumbnail_url=None,
                )
            ],
        )
        handler.parser.parse = MagicMock(return_value=content)

        inline_query = _make_inline_query("https://x.com/user/status/1")
        update = MagicMock()
        update.inline_query = inline_query

        await handler.handle(update, None)

        results = inline_query.answer.call_args[0][0]
        gif_results = [r for r in results if isinstance(r, InlineQueryResultGif)]
        assert gif_results, "No InlineQueryResultGif in results"
        assert gif_results[0].thumbnail_url == "http://cdn.test/anim.gif"

    @pytest.mark.asyncio
    async def test_gif_with_explicit_thumbnail_uses_that_url(self):
        from telegram import InlineQueryResultGif

        from core.domain.entity import GIF, Content

        handler = _make_handler()
        content = Content(
            backlink=MagicMock(url="https://x.com/u/status/1"),
            media=[
                GIF(
                    resource_url="http://cdn.test/anim.gif",
                    mime_type="image/gif",
                    thumbnail_url="http://cdn.test/thumb.jpg",
                )
            ],
        )
        handler.parser.parse = MagicMock(return_value=content)

        inline_query = _make_inline_query("https://x.com/user/status/1")
        update = MagicMock()
        update.inline_query = inline_query

        await handler.handle(update, None)

        results = inline_query.answer.call_args[0][0]
        gif_results = [r for r in results if isinstance(r, InlineQueryResultGif)]
        assert gif_results[0].thumbnail_url == "http://cdn.test/thumb.jpg"


class TestVideoThumbnailFallback:
    @pytest.mark.asyncio
    async def test_video_without_thumbnail_uses_resource_url(self):
        from telegram import InlineQueryResultVideo

        from core.domain.entity import Content, Video

        handler = _make_handler()
        content = Content(
            backlink=MagicMock(url="https://x.com/u/status/1"),
            media=[
                Video(
                    resource_url="http://cdn.test/vid.mp4",
                    mime_type="video/mp4",
                    thumbnail_url=None,
                )
            ],
        )
        handler.parser.parse = MagicMock(return_value=content)

        inline_query = _make_inline_query("https://x.com/user/status/1")
        update = MagicMock()
        update.inline_query = inline_query

        await handler.handle(update, None)

        results = inline_query.answer.call_args[0][0]
        video_results = [r for r in results if isinstance(r, InlineQueryResultVideo)]
        assert video_results, "No InlineQueryResultVideo in results"
        assert video_results[0].thumbnail_url == "http://cdn.test/vid.mp4"

    @pytest.mark.asyncio
    async def test_video_with_explicit_thumbnail_uses_that_url(self):
        from telegram import InlineQueryResultVideo

        from core.domain.entity import Content, Video

        handler = _make_handler()
        content = Content(
            backlink=MagicMock(url="https://x.com/u/status/1"),
            media=[
                Video(
                    resource_url="http://cdn.test/vid.mp4",
                    mime_type="video/mp4",
                    thumbnail_url="http://cdn.test/thumb.jpg",
                )
            ],
        )
        handler.parser.parse = MagicMock(return_value=content)

        inline_query = _make_inline_query("https://x.com/user/status/1")
        update = MagicMock()
        update.inline_query = inline_query

        await handler.handle(update, None)

        results = inline_query.answer.call_args[0][0]
        video_results = [r for r in results if isinstance(r, InlineQueryResultVideo)]
        assert video_results[0].thumbnail_url == "http://cdn.test/thumb.jpg"
