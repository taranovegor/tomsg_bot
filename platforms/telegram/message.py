import asyncio
import logging
from io import BufferedReader
from typing import Optional
from urllib.parse import urlparse

from telegram import (
    Update,
    InputMediaPhoto,
    InputMediaAnimation,
    InputMediaVideo,
    InputMedia,
)
from telegram.constants import ChatAction, ParseMode, ChatType
from telegram.ext import ContextTypes

from infra.analytics.analytics import Events, Event, Analytics
from core.domain.entity import Entity, Video, GIF, Photo, FileInfo, VideoMeta, PipelineResult
from core.exceptions import InvalidUrlError, ParserNotFoundError
from core.pipeline import Pipeline
from core.ports.delivery import Delivery
from platforms.telegram import MEDIA_GROUP_CHUNK_SIZE
from platforms.telegram.renderer import MessageRenderer


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and (exc := task.exception()):
        logging.error("Background send task failed", exc_info=exc)


class TelegramDelivery(Delivery):
    """
    Send PipelineResult to Telegram: render caption, open files, separate
    GIFs from photo/video, chunk into media groups, and call the transport.
    """

    def __init__(
        self,
        renderer: MessageRenderer,
        chunk_size: int = MEDIA_GROUP_CHUNK_SIZE,
    ):
        self.renderer = renderer
        self.chunk_size = chunk_size

    async def send(
        self, target, result: PipelineResult
    ) -> None:
        kwargs = {"parse_mode": ParseMode.HTML, "do_quote": True}
        text = self.renderer.render_with_link(result.content)

        if not result.resolved_media:
            await target.reply_text(
                text, disable_web_page_preview=True, **kwargs
            )
            return

        all_files_to_close = []
        all_files_to_remove = []

        try:
            prepared = await asyncio.gather(
                *[
                    self._prepare_media(media, fi, result.video_meta)
                    for media, fi in result.resolved_media
                ],
                return_exceptions=True,
            )

            regular_media = []
            gif_inputs = []

            for item in prepared:
                if isinstance(item, Exception):
                    logging.warning("Failed to prepare media: %s", item)
                    continue
                media_input, files_to_close, files_to_remove = item
                if media_input is None:
                    continue
                all_files_to_close.extend(files_to_close)
                all_files_to_remove.extend(files_to_remove)
                if isinstance(media_input, InputMediaAnimation):
                    gif_inputs.append(media_input)
                else:
                    regular_media.append(media_input)

            if not regular_media and not gif_inputs:
                await target.reply_text(
                    text, disable_web_page_preview=True, **kwargs
                )
                return

            caption_sent = False

            for i in range(0, len(regular_media), self.chunk_size):
                chunk = regular_media[i : i + self.chunk_size]
                is_last_regular = i + self.chunk_size >= len(regular_media)
                use_caption = is_last_regular and not gif_inputs
                try:
                    await target.reply_media_group(
                        chunk,
                        caption=text if use_caption else None,
                        **kwargs,
                    )
                    if use_caption:
                        caption_sent = True
                except Exception as e:
                    logging.error("Failed to send media chunk: %s", e)

            for idx, gif_input in enumerate(gif_inputs):
                is_last_gif = idx == len(gif_inputs) - 1
                use_caption = is_last_gif and not caption_sent
                try:
                    await target.reply_animation(
                        gif_input.media,
                        caption=text if use_caption else None,
                        **kwargs,
                    )
                    if use_caption:
                        caption_sent = True
                except Exception as e:
                    logging.error("Failed to send GIF: %s", e)

        finally:
            for fh in all_files_to_close:
                try:
                    await asyncio.to_thread(fh.close)
                except Exception as e:
                    logging.exception(
                        "Failed to close file handler: %s", e
                    )

            for path in all_files_to_remove:
                try:
                    if path.exists():
                        await asyncio.to_thread(path.unlink)
                except Exception as e:
                    logging.exception(
                        "Failed to remove file %s: %s", path, e
                    )

    async def _prepare_media(
        self,
        media: Entity,
        file_info: FileInfo,
        video_meta: dict[str, VideoMeta],
    ) -> Optional[tuple[InputMedia, list[BufferedReader], list]]:
        files_to_close = []
        files_to_remove = []

        file_handler = await asyncio.to_thread(
            lambda: open(file_info.path, "rb")
        )
        files_to_close.append(file_handler)
        files_to_remove.append(file_info.path)

        if isinstance(media, Photo):
            return InputMediaPhoto(file_handler), files_to_close, files_to_remove

        if isinstance(media, GIF):
            return (
                InputMediaAnimation(file_handler),
                files_to_close,
                files_to_remove,
            )

        if isinstance(media, Video):
            meta = video_meta.get(media.resource_url)
            return (
                InputMediaVideo(
                    file_handler,
                    width=meta.width if meta else None,
                    height=meta.height if meta else None,
                    duration=meta.duration if meta else None,
                    supports_streaming=True,
                    thumbnail=media.thumbnail_url,
                ),
                files_to_close,
                files_to_remove,
            )

        return None


class MessageHandler:
    """
    Handle private Telegram messages: validate, run neutral pipeline,
    and dispatch result to TelegramDelivery.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        delivery: Delivery,
        analytics: Analytics,
        platform: str = "telegram",
    ):
        self.pipeline = pipeline
        self.delivery = delivery
        self.analytics = analytics
        self.platform = platform

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = update.message
        if not message:
            return

        if ChatType.PRIVATE != update.effective_chat.type:
            return

        text = message.text or ""
        if not text:
            return

        events = Events(message.from_user.id, self.platform, "message")

        asyncio.create_task(
            context.bot.send_chat_action(
                update.effective_chat.id, ChatAction.TYPING
            )
        )

        kwargs = {"parse_mode": ParseMode.HTML, "do_quote": True}

        try:
            result = await self.pipeline.run(text)
            events.add(Event("page_view").add("page_location", text))
            task = asyncio.create_task(self.delivery.send(message, result))
            task.add_done_callback(_log_task_exception)
        except InvalidUrlError as e:
            logging.warning("Invalid URL received: %s", text)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
            )
            await message.reply_text(
                "Введённый текст не является корректным URL.", **kwargs
            )
        except ParserNotFoundError as e:
            hostname = urlparse(text).netloc
            logging.warning("Parser not found for hostname: %s", hostname)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
                .add("hostname", hostname)
            )
            await message.reply_text(
                "Ссылка с этого ресурса ещё не поддерживается.", **kwargs
            )
        except Exception as e:
            logging.error(
                "Exception while processing text: %s", text, exc_info=True
            )
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
            )
            await message.reply_text(
                "Произошла ошибка при обработке вашего запроса. Повторите позже.",
                **kwargs,
            )

        await self.analytics.log(events)
