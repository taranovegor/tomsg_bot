"""
Tests for message handling.

GIF (InputMediaAnimation) must not be put into reply_media_group alongside
photos/videos. Telegram rejects this. GIFs must be sent via
reply_animation as individual messages.

asyncio.create_task calls must have a done-callback so
exceptions inside _send_content are not silently swallowed.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_handler():
    from core.telega.message import MessageHandler
    from core.telega.renderer import MessageRenderer

    analytics = MagicMock()
    analytics.log = AsyncMock()
    return MessageHandler(
        parser=MagicMock(),
        renderer=MessageRenderer(),
        file_resolver=MagicMock(),
        video_processor=MagicMock(),
        analytics=analytics,
    )


# ---------------------------------------------------------------------------
# GIF routing
# ---------------------------------------------------------------------------

class TestGifSentSeparately:
    @pytest.mark.asyncio
    async def test_gif_only_uses_reply_animation_not_reply_media_group(self, tmp_path):
        from core.parser.entity import Content, GIF
        from core.files.entity import FileInfo

        gif_path = tmp_path / "anim.mp4"
        gif_path.write_bytes(b"\x00" * 16)

        handler = _make_handler()
        content = Content(
            backlink=MagicMock(url="https://x.com/u/status/1"),
            media=[GIF(resource_url="http://cdn.test/anim.gif",
                       mime_type="image/gif",
                       thumbnail_url="http://cdn.test/thumb.jpg")],
        )
        handler.file_resolver.resolve = AsyncMock(
            return_value=FileInfo(path=gif_path, size=16, mime_type="image/gif")
        )

        message = MagicMock()
        message.reply_media_group = AsyncMock()
        message.reply_animation = AsyncMock()
        message.reply_text = AsyncMock()

        await handler._send_content(message, content)

        message.reply_animation.assert_called_once()
        message.reply_media_group.assert_not_called()

    @pytest.mark.asyncio
    async def test_mixed_photo_and_gif_routes_correctly(self, tmp_path):
        from core.parser.entity import Content, GIF, Photo
        from core.files.entity import FileInfo

        photo_path = tmp_path / "photo.jpg"
        gif_path = tmp_path / "anim.mp4"
        photo_path.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)
        gif_path.write_bytes(b"\x00" * 16)

        handler = _make_handler()
        content = Content(
            backlink=MagicMock(url="https://x.com/u/status/1"),
            media=[
                Photo(resource_url="http://cdn.test/photo.jpg"),
                GIF(resource_url="http://cdn.test/anim.gif",
                    mime_type="image/gif",
                    thumbnail_url="http://cdn.test/thumb.jpg"),
            ],
        )

        fi_photo = FileInfo(path=photo_path, size=103, mime_type="image/jpeg")
        fi_gif = FileInfo(path=gif_path, size=16, mime_type="image/gif")

        async def resolve_side_effect(url):
            return fi_photo if "photo" in url else fi_gif

        handler.file_resolver.resolve = resolve_side_effect

        message = MagicMock()
        message.reply_media_group = AsyncMock()
        message.reply_animation = AsyncMock()
        message.reply_text = AsyncMock()

        await handler._send_content(message, content)

        message.reply_media_group.assert_called_once()
        message.reply_animation.assert_called_once()

    @pytest.mark.asyncio
    async def test_caption_is_sent_even_when_only_gif(self, tmp_path):
        """When the only media is a GIF, the caption must still be included."""
        from core.parser.entity import Content, GIF
        from core.files.entity import FileInfo

        gif_path = tmp_path / "anim.mp4"
        gif_path.write_bytes(b"\x00" * 16)

        handler = _make_handler()
        content = Content(
            backlink=MagicMock(url="https://x.com/u/status/1"),
            text="hello world",
            media=[GIF(resource_url="http://cdn.test/anim.gif",
                       mime_type="image/gif",
                       thumbnail_url="http://cdn.test/thumb.jpg")],
        )
        handler.file_resolver.resolve = AsyncMock(
            return_value=FileInfo(path=gif_path, size=16, mime_type="image/gif")
        )

        message = MagicMock()
        message.reply_animation = AsyncMock()
        message.reply_text = AsyncMock()
        message.reply_media_group = AsyncMock()

        await handler._send_content(message, content)

        call_kwargs = message.reply_animation.call_args.kwargs
        assert call_kwargs.get("caption") is not None


# ---------------------------------------------------------------------------
# task done-callback
# ---------------------------------------------------------------------------

class TestSendContentTaskCallback:
    @pytest.mark.asyncio
    async def test_log_task_exception_callback_logs_on_failure(self):
        """
        _log_task_exception (the done-callback registered by handle) must call
        logging.error when the task raises. This verifies the callback itself
        works: exceptions are not silently dropped.
        """
        from unittest.mock import patch
        from core.telega.message import _log_task_exception

        async def failing():
            raise RuntimeError("deliberate explosion")

        task = asyncio.create_task(failing())
        task.add_done_callback(_log_task_exception)

        with patch("core.telega.message.logging.error") as mock_error:
            # Wait for the task to finish so the callback fires inside the patch
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=1.0)
            except (RuntimeError, asyncio.TimeoutError):
                pass

        assert mock_error.called, (
            "logging.error was never called — exception from the task was silently dropped"
        )
        call_str = str(mock_error.call_args_list)
        assert "Background" in call_str, f"Unexpected call args: {call_str}"

    @pytest.mark.asyncio
    async def test_log_task_exception_callback_silent_on_success(self):
        """Done-callback must not log anything when the task succeeds."""
        from unittest.mock import patch
        from core.telega.message import _log_task_exception

        async def succeeding():
            return 42

        task = asyncio.create_task(succeeding())
        task.add_done_callback(_log_task_exception)

        with patch("core.telega.message.logging.error") as mock_error:
            await asyncio.wait_for(asyncio.shield(task), timeout=1.0)

        mock_error.assert_not_called()

