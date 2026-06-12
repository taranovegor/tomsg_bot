"""
Tests for message handling.

GIF (InputMediaAnimation) must not be put into reply_media_group alongside
photos/videos. Telegram rejects this. GIFs must be sent via
reply_animation as individual messages.

asyncio.create_task calls must have a done-callback so
exceptions inside _send_content are not silently swallowed.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.domain.entity import Content, GIF, Photo, Link, FileInfo, PipelineResult
from core.exceptions import InvalidUrlError, ParserNotFoundError
from platforms.telegram.message import TelegramDelivery, MessageHandler


def _make_delivery():
    from platforms.telegram.renderer import MessageRenderer

    return TelegramDelivery(renderer=MessageRenderer())


# ---------------------------------------------------------------------------
# GIF routing
# ---------------------------------------------------------------------------


class TestGifSentSeparately:
    @pytest.mark.asyncio
    async def test_gif_only_uses_reply_animation_not_reply_media_group(self, tmp_path):
        gif_path = tmp_path / "anim.mp4"
        gif_path.write_bytes(b"\x00" * 16)

        delivery = _make_delivery()
        content = Content(
            backlink=Link(url="https://x.com/u/status/1"),
            media=[GIF(resource_url="http://cdn.test/anim.gif",
                       mime_type="image/gif",
                       thumbnail_url="http://cdn.test/thumb.jpg")],
        )
        result = PipelineResult(
            content=content,
            resolved_media=[
                (GIF(resource_url="http://cdn.test/anim.gif",
                     mime_type="image/gif",
                     thumbnail_url="http://cdn.test/thumb.jpg"),
                 FileInfo(path=gif_path, size=16, mime_type="image/gif")),
            ],
        )

        message = MagicMock()
        message.reply_media_group = AsyncMock()
        message.reply_animation = AsyncMock()
        message.reply_text = AsyncMock()

        await delivery.send(message, result)

        message.reply_animation.assert_called_once()
        message.reply_media_group.assert_not_called()

    @pytest.mark.asyncio
    async def test_mixed_photo_and_gif_routes_correctly(self, tmp_path):
        photo_path = tmp_path / "photo.jpg"
        gif_path = tmp_path / "anim.mp4"
        photo_path.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)
        gif_path.write_bytes(b"\x00" * 16)

        delivery = _make_delivery()
        content = Content(
            backlink=Link(url="https://x.com/u/status/1"),
            media=[
                Photo(resource_url="http://cdn.test/photo.jpg"),
                GIF(resource_url="http://cdn.test/anim.gif",
                    mime_type="image/gif",
                    thumbnail_url="http://cdn.test/thumb.jpg"),
            ],
        )
        result = PipelineResult(
            content=content,
            resolved_media=[
                (Photo(resource_url="http://cdn.test/photo.jpg"),
                 FileInfo(path=photo_path, size=103, mime_type="image/jpeg")),
                (GIF(resource_url="http://cdn.test/anim.gif",
                     mime_type="image/gif",
                     thumbnail_url="http://cdn.test/thumb.jpg"),
                 FileInfo(path=gif_path, size=16, mime_type="image/gif")),
            ],
        )

        message = MagicMock()
        message.reply_media_group = AsyncMock()
        message.reply_animation = AsyncMock()
        message.reply_text = AsyncMock()

        await delivery.send(message, result)

        message.reply_media_group.assert_called_once()
        message.reply_animation.assert_called_once()

    @pytest.mark.asyncio
    async def test_caption_is_sent_even_when_only_gif(self, tmp_path):
        gif_path = tmp_path / "anim.mp4"
        gif_path.write_bytes(b"\x00" * 16)

        delivery = _make_delivery()
        content = Content(
            backlink=Link(url="https://x.com/u/status/1"),
            text="hello world",
            media=[GIF(resource_url="http://cdn.test/anim.gif",
                       mime_type="image/gif",
                       thumbnail_url="http://cdn.test/thumb.jpg")],
        )
        result = PipelineResult(
            content=content,
            resolved_media=[
                (GIF(resource_url="http://cdn.test/anim.gif",
                     mime_type="image/gif",
                     thumbnail_url="http://cdn.test/thumb.jpg"),
                 FileInfo(path=gif_path, size=16, mime_type="image/gif")),
            ],
        )

        message = MagicMock()
        message.reply_animation = AsyncMock()
        message.reply_text = AsyncMock()
        message.reply_media_group = AsyncMock()

        await delivery.send(message, result)

        call_kwargs = message.reply_animation.call_args.kwargs
        assert call_kwargs.get("caption") is not None


# ---------------------------------------------------------------------------
# task done-callback
# ---------------------------------------------------------------------------


class TestSendContentTaskCallback:
    @pytest.mark.asyncio
    async def test_log_task_exception_callback_logs_on_failure(self):
        from platforms.telegram.message import _log_task_exception

        async def failing():
            raise RuntimeError("deliberate explosion")

        task = asyncio.create_task(failing())
        task.add_done_callback(_log_task_exception)

        with patch("platforms.telegram.message.logging.error") as mock_error:
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
        from platforms.telegram.message import _log_task_exception

        async def succeeding():
            return 42

        task = asyncio.create_task(succeeding())
        task.add_done_callback(_log_task_exception)

        with patch("platforms.telegram.message.logging.error") as mock_error:
            await asyncio.wait_for(asyncio.shield(task), timeout=1.0)

        mock_error.assert_not_called()


# ---------------------------------------------------------------------------
# MessageHandler.handle() — orchestration
# ---------------------------------------------------------------------------


class FakePipeline:
    def __init__(self):
        self.result = PipelineResult(
            content=Content(backlink=Link(url="https://example.com"), text="ok"),
        )

    async def run(self, url: str) -> PipelineResult:
        return self.result


class FakeFailingPipeline:
    def __init__(self, exc: Exception):
        self._exc = exc

    async def run(self, url: str) -> PipelineResult:
        raise self._exc


def _make_handler(pipeline, delivery=None):
    analytics = MagicMock()
    analytics.log = AsyncMock()
    if delivery is None:
        delivery = MagicMock()
        delivery.send = AsyncMock()
    return MessageHandler(
        pipeline=pipeline,
        delivery=delivery,
        analytics=analytics,
        platform="telegram",
    )


def _make_update(text: str):
    update = MagicMock()
    msg = MagicMock()
    msg.text = text
    msg.from_user.id = 42
    msg.reply_text = AsyncMock()
    msg.reply_animation = AsyncMock()
    msg.reply_media_group = AsyncMock()
    update.message = msg
    update.effective_chat.type = "private"
    return update, msg


def _make_context():
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    return context


class TestMessageHandlerHandle:
    @pytest.mark.asyncio
    async def test_invalid_url_replies_and_logs_exception_event(self):
        pipeline = FakeFailingPipeline(InvalidUrlError())
        handler = _make_handler(pipeline)
        update, msg = _make_update("not a url")
        context = _make_context()

        await handler.handle(update, context)

        msg.reply_text.assert_called_once()
        reply_text = msg.reply_text.call_args[0][0]
        assert "не является корректным URL" in reply_text

        assert handler.analytics.log.called
        log_call = handler.analytics.log.call_args[0][0]
        assert any(e.name == "exception" for e in log_call)

    @pytest.mark.asyncio
    async def test_parser_not_found_replies_and_logs_hostname(self):
        pipeline = FakeFailingPipeline(ParserNotFoundError("no parser"))
        handler = _make_handler(pipeline)
        update, msg = _make_update("https://unsupported.example.com")
        context = _make_context()

        await handler.handle(update, context)

        msg.reply_text.assert_called_once()
        reply_text = msg.reply_text.call_args[0][0]
        assert "не поддерживается" in reply_text

        log_call = handler.analytics.log.call_args[0][0]
        exception_events = [e for e in log_call if e.name == "exception"]
        assert len(exception_events) == 1
        assert "hostname" in exception_events[0]
        assert "unsupported" in str(exception_events[0]["hostname"])

    @pytest.mark.asyncio
    async def test_success_schedules_delivery_and_logs_once(self):
        pipeline = FakePipeline()
        delivery = MagicMock()
        delivery.send = AsyncMock()
        handler = _make_handler(pipeline, delivery=delivery)
        update, msg = _make_update("https://example.com/post")
        context = _make_context()

        await handler.handle(update, context)

        delivery.send.assert_called_once()
        args, _ = delivery.send.call_args
        assert args[0] is msg
        assert args[1] is pipeline.result

        assert handler.analytics.log.call_count == 1
        log_call = handler.analytics.log.call_args[0][0]
        assert any(e.name == "page_view" for e in log_call)

    @pytest.mark.asyncio
    async def test_platform_passed_to_events(self):
        pipeline = FakePipeline()
        delivery = MagicMock()
        delivery.send = AsyncMock()
        handler = _make_handler(pipeline, delivery=delivery)
        update, msg = _make_update("https://example.com/post")
        context = _make_context()

        events_instance = MagicMock()
        events_instance.add = MagicMock(return_value=events_instance)

        with patch("platforms.telegram.message.Events", return_value=events_instance):
            await handler.handle(update, context)

        from infra.analytics.analytics import Events as EventsReal
        args = events_instance.add.call_args_list
        page_view_calls = [a for a in args if a[0][0].name == "page_view"]
        assert len(page_view_calls) == 1
        assert page_view_calls[0][0][0]["page_location"] == "https://example.com/post"
