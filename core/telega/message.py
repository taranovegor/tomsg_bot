import asyncio
import logging
from io import BufferedReader
from typing import Tuple, Optional
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

from core.analytics.analytics import Events, Event, Analytics
from core import Parser, ParserNotFoundError
from core.files.entity import FileInfo
from core.files.resolver import FileResolver
from core.media.processor import VideoProcessor
from core.parser.entity import Entity, Video, GIF, Photo
from core.parser.exception import InvalidUrlError
from core.telega.renderer import MessageRenderer
from core.utils.urls import is_valid_url


def _log_task_exception(task: asyncio.Task) -> None:
    """Done-callback that logs any unhandled exception from a fire-and-forget task."""
    if not task.cancelled() and (exc := task.exception()):
        logging.error("Background _send_content task failed", exc_info=exc)


class MessageHandler:
    """
    Handle private messages that contain URLs: validate, parse, render and send.
    """

    def __init__(
        self,
        parser: Parser,
        renderer: MessageRenderer,
        file_resolver: FileResolver,
        video_processor: VideoProcessor,
        analytics: Analytics,
    ):
        self.parser = parser
        self.renderer = renderer
        self.file_resolver = file_resolver
        self.video_processor = video_processor
        self.analytics = analytics

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        if not message:
            return

        if ChatType.PRIVATE != update.effective_chat.type:
            return

        text = message.text or ""
        if not text:
            return

        events = Events(message.from_user.id, "telegram", "message")

        asyncio.create_task(
            context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        )

        kwargs = {"parse_mode": ParseMode.HTML, "do_quote": True}

        if not is_valid_url(text):
            logging.warning("Invalid URL received: %s", text)
            e = InvalidUrlError()
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
            )
            await message.reply_text(
                "Введённый текст не является корректным URL.", **kwargs
            )
            await self.analytics.log(events)
            return

        hostname = urlparse(text).netloc
        try:
            logging.info("Processing valid URL from hostname: %s", hostname)
            events.add(Event("page_view").add("page_location", text))
            content = await asyncio.to_thread(self.parser.parse, text)
            logging.debug("Successfully parsed entity for text: %s", text)
            task = asyncio.create_task(self._send_content(message, content))
            task.add_done_callback(_log_task_exception)
        except ParserNotFoundError as e:
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
            logging.error("Exception while processing text: %s", text, exc_info=True)
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

    async def _send_content(self, message, content):
        kwargs = {"parse_mode": ParseMode.HTML, "do_quote": True}
        text = self.renderer.render_with_link(content)

        if not content.media:
            await message.reply_text(text, disable_web_page_preview=True, **kwargs)
            return

        all_files_to_close = []
        all_files_to_remove = []

        try:
            resolve_tasks = [
                self.file_resolver.resolve(m.resource_url) for m in content.media
            ]
            raw_results = await asyncio.gather(*resolve_tasks, return_exceptions=True)

            successful_pairs = []
            for media, res in zip(content.media, raw_results):
                if isinstance(res, Exception):
                    logging.warning("Failed to resolve %s: %s", media.resource_url, res)
                    continue
                successful_pairs.append((media, res))

            if not successful_pairs:
                await message.reply_text(text, disable_web_page_preview=True, **kwargs)
                return

            prepared = await asyncio.gather(
                *[self._prepare_media(media, fi) for media, fi in successful_pairs],
                return_exceptions=True,
            )

            # Telegram forbids InputMediaAnimation inside a media group that contains
            # photos or videos — GIFs must be sent as individual reply_animation calls.
            regular_media = []  # InputMediaPhoto / InputMediaVideo
            gif_inputs = []     # InputMediaAnimation

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
                await message.reply_text(text, disable_web_page_preview=True, **kwargs)
                return

            caption_sent = False
            chunk_size = 10

            # Send photos and videos as media groups
            for i in range(0, len(regular_media), chunk_size):
                chunk = regular_media[i : i + chunk_size]
                is_last_regular = i + chunk_size >= len(regular_media)
                use_caption = is_last_regular and not gif_inputs
                try:
                    await message.reply_media_group(
                        chunk, caption=text if use_caption else None, **kwargs
                    )
                    if use_caption:
                        caption_sent = True
                except Exception as e:
                    logging.error("Failed to send media chunk: %s", e)

            # Send each GIF as a standalone message
            for idx, gif_input in enumerate(gif_inputs):
                is_last_gif = idx == len(gif_inputs) - 1
                use_caption = is_last_gif and not caption_sent
                try:
                    await message.reply_animation(
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
                    logging.exception("Failed to close file handler: %s", e)

            for path in all_files_to_remove:
                try:
                    if path.exists():
                        await asyncio.to_thread(path.unlink)
                except Exception as e:
                    logging.exception("Failed to remove file %s: %s", path, e)

    async def _prepare_media(
        self, media: Entity, file_info: FileInfo
    ) -> Optional[Tuple[InputMedia, list[BufferedReader], list]]:
        """
        Open files and prepare InputMedia objects; perform video processing asynchronously.
        Returns:
            - InputMedia object
            - List of file handles to close
            - List of file paths to remove after sending
        """
        files_to_close = []
        files_to_remove = []

        file_handler = await asyncio.to_thread(lambda: open(file_info.path, "rb"))
        files_to_close.append(file_handler)
        files_to_remove.append(file_info.path)

        if isinstance(media, Photo):
            return InputMediaPhoto(file_handler), files_to_close, files_to_remove

        if isinstance(media, GIF):
            return InputMediaAnimation(file_handler), files_to_close, files_to_remove

        if isinstance(media, Video):
            video_meta = await self.video_processor.process_video(file_info.path)

            return (
                InputMediaVideo(
                    file_handler,
                    width=video_meta.width,
                    height=video_meta.height,
                    duration=video_meta.duration,
                    supports_streaming=True,
                    thumbnail=media.thumbnail_url,
                ),
                files_to_close,
                files_to_remove,
            )

        return None
