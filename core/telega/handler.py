import logging
import re
from urllib.parse import urlparse

import validators
from telegram import (
    Update,
    InlineQueryResult,
    InputTextMessageContent,
    InlineQueryResultArticle,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from core import Parser, InvalidUrlError, ParserNotFoundError
from core.analytics.analytics import Analytics, Events, Event
from core.telega.inline import InlineResultsFactory
import aiohttp
import tempfile
import os
import asyncio
import ffmpeg  # add ffmpeg-python


class InlineHandler:
    """Handles inline queries, parses URLs, and generates appropriate results."""

    URL_REGEX = re.compile(
        r"^(https?://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(/\S*)?$"
    )

    def __init__(
        self,
        parser: Parser,
        results_factory: InlineResultsFactory,
        analytics: Analytics,
    ):
        """Initializes the inline query handler with a parser, results factory, and analytics service."""
        self.parser = parser
        self.results_factory = results_factory
        self.analytics = analytics

    async def inline_query(self, update: Update, _):
        """Handles an inline query by validating the query and returning results or errors."""
        query = update.inline_query.query
        logging.debug("Received inline query: %s", query)
        if not query:
            logging.debug("Empty query received")
            return

        events = Events(update.inline_query.from_user.id)

        if self._is_valid_url(query):
            results = await self._handle_valid_url(query, events)
        else:
            results = self._handle_invalid_url(query, events)

        await update.inline_query.answer(results=results, cache_time=0)
        await self.analytics.log(events)
        logging.info("Inline query processed successfully")

    def _is_valid_url(self, query: str) -> bool:
        """Checks if the query is a valid URL."""
        is_valid = validators.url(query) or self.URL_REGEX.match(query)
        logging.debug("URL validation result for '%s': %s", query, is_valid)
        return is_valid

    async def _handle_valid_url(
        self, query: str, events: Events
    ) -> list[InlineQueryResult]:
        """Handles a valid URL query by parsing it and generating results."""
        hostname = urlparse(query).netloc

        events.add(Event("page_view").add("page_location", query))
        logging.info("Processing valid URL from hostname: %s", hostname)
        try:
            entity = self.parser.parse(query)
            logging.debug("Successfully parsed entity for query: %s", query)
            return self.results_factory.create(entity)
        except ParserNotFoundError as e:
            logging.warning("Parser not found for hostname: %s", hostname)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
                .add("hostname", hostname)
            )
            return self._error_result(
                "no_parser_found",
                "🔗 Ссылка не поддерживается",
                "К сожалению, ссылка с этого ресурса еще не поддерживается.",
                query,
            )
        except Exception as e:
            logging.error("Exception while processing query: %s", query, exc_info=True)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
            )
            return self._error_result(
                "exception",
                "⚠️ Ошибка обработки",
                "Произошла ошибка при обработке вашего запроса. Повторите попытку позже.",
                query,
            )

    def _handle_invalid_url(
        self, query: str, events: Events
    ) -> list[InlineQueryResult]:
        """Handles an invalid URL query by generating an error result."""
        logging.warning("Invalid URL received: %s", query)
        e = InvalidUrlError()
        events.add(
            Event("exception")
            .add("description", str(e))
            .add("type", type(e).__name__)
        )
        return self._error_result(
            "invalid_url",
            "❌ Невозможно обработать",
            "Введенный текст не содержит корректной ссылки для обработки.",
            query,
        )

    @staticmethod
    def _error_result(
        identifier: str, title: str, description: str, query: str
    ) -> list[InlineQueryResult]:
        """Generates an error result for inline queries."""
        logging.debug("Generating error result: %s", identifier)
        return [
            InlineQueryResultArticle(
                id=f"e_{identifier}",
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=f"{query}\n\n❗️Это сообщение введено пользователем, бот не отвечает за его содержание.",
                ),
            ),
        ]


class ChatHandler:
    """Handles chat messages (non-inline). Processes URLs similarly to inline handler.

    Behaviour:
    - If the message contains a valid URL, parse and send formatted content.
    - If the message doesn't contain a valid URL and chat is a group/supergroup/channel -> ignore.
    - If the message doesn't contain a valid URL and chat is private -> reply with an error message.
    """

    SIMPLE_URL_REGEX = re.compile(r"https?://\S+")
    MAX_TELEGRAM_MULTIPART_SIZE = 20 * 1024 * 1024  # 20 MB

    def __init__(self, parser: Parser, results_factory: InlineResultsFactory, analytics: Analytics):
        self.parser = parser
        self.results_factory = results_factory
        self.analytics = analytics

    async def chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message
        if not msg or not msg.text:
            logging.debug("No text message to process in chat_message")
            return

        text = msg.text.strip()
        user_id = msg.from_user.id if msg.from_user else None
        events = Events(user_id)

        # Try to extract a URL from the message text
        url = self._extract_url(text)
        if not url:
            # No valid URL found
            logging.warning("Invalid or missing URL in chat message: %s", text)
            events.add(Event("exception").add("description", str(InvalidUrlError())).add("type", InvalidUrlError.__name__))

            # If chat is group-like, ignore silently
            chat_type = msg.chat.type
            if chat_type in ("group", "supergroup", "channel"):
                logging.info("Ignoring invalid URL in group chat (chat_id=%s)", msg.chat.id)
                await self.analytics.log(events)
                return

            # Private chat -> send error reply
            await msg.reply_text(
                f"{text}\n\n❗️Это сообщение введено пользователем, бот не отвечает за его содержание.",
            )
            await self.analytics.log(events)
            return

        # Valid URL found; proceed to parse
        hostname = urlparse(url).netloc
        events.add(Event("page_view").add("page_location", url))
        logging.info("Processing chat URL from hostname: %s", hostname)

        try:
            entity = self.parser.parse(url)
            logging.debug("Successfully parsed entity for chat message: %s", url)

            # Build main message text using the same formatter as inline results
            formatter = self.results_factory.formatter
            body = formatter.generate_text_description(entity)
            backlink = formatter.format_link_as_html(entity.backlink)
            message_text = formatter.combine_text_with_link(body, "📄", backlink)

            # Send the textual content first
            # await msg.reply_text(message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

            # If there is media, try to send them (send first media as an example)
            if getattr(entity, "media", None):
                for media in entity.media:
                    mtype = media.type()
                    caption = formatter.combine_text_with_link(body, {"photo": "🖼", "video": "📺", "gif": "🎞️"}.get(mtype, ""), backlink)
                    if mtype == "photo":
                        await msg.reply_photo(media.resource_url, caption=caption, parse_mode=ParseMode.HTML)
                    elif mtype == "video":
                        # handle large video via multipart upload if needed
                        await self._send_media_with_multipart_if_needed(msg, media.resource_url, media_type="video", caption=caption)
                    elif mtype == "gif":
                        await msg.reply_animation(media.resource_url, caption=caption, parse_mode=ParseMode.HTML)

            await self.analytics.log(events)
            logging.info("Chat message processed successfully")

        except ParserNotFoundError as e:
            logging.warning("Parser not found for hostname: %s", hostname)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
                .add("hostname", hostname)
            )
            await msg.reply_text(
                "🔗 Ссылка не поддерживается\nК сожалению, ссылка с этого ресурса еще не поддерживается.",
            )
            await self.analytics.log(events)

        except Exception as e:
            logging.error("Exception while processing chat message: %s", url, exc_info=True)
            events.add(
                Event("exception").add("description", str(e)).add("type", type(e).__name__)
            )
            await msg.reply_text(
                "⚠️ Ошибка обработки\nПроизошла ошибка при обработке вашего запроса. Повторите попытку позже.",
            )
            await self.analytics.log(events)

    def _extract_url(self, text: str) -> str | None:
        """Attempts to extract the first URL from a text block.

        Returns the URL string or None if not found/invalid.
        """
        # If the whole text is a URL, accept it
        if validators.url(text):
            return text

        # Look for simple http(s):// tokens inside the text
        m = self.SIMPLE_URL_REGEX.search(text)
        if m:
            # strip trailing punctuation
            url = m.group(0).rstrip('.,)\"\'')
            return url

        # Try token-based validation
        for token in text.split():
            candidate = token.strip('()[]\n\r\t')
            if validators.url(candidate):
                return candidate

        return None

    # new helpers -------------------------------------------------------------

    async def _get_remote_size(self, url: str) -> int | None:
        """Try to get remote resource size in bytes. Returns None when unknown."""
        try:
            async with aiohttp.ClientSession() as session:
                # try HEAD first
                try:
                    async with session.head(url, timeout=10) as resp:
                        if resp.status in (200, 206):
                            cl = resp.headers.get("Content-Length")
                            if cl and cl.isdigit():
                                return int(cl)
                except Exception:
                    # HEAD might be unsupported; fallthrough to ranged GET
                    pass

                # Try a ranged GET to get headers
                headers = {"Range": "bytes=0-0"}
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status in (200, 206):
                        cl = resp.headers.get("Content-Range") or resp.headers.get("Content-Length")
                        if cl:
                            # Content-Range example: bytes 0-0/12345678
                            if "/" in cl:
                                try:
                                    total = int(cl.split("/")[-1])
                                    return total
                                except Exception:
                                    pass
                            if cl.isdigit():
                                return int(cl)
        except Exception:
            logging.debug("Failed to determine remote size for %s", url, exc_info=True)
        return None

    async def _download_to_tempfile(self, url: str) -> str:
        """Stream-download remote url to a temp file and return local path."""
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=None) as resp:
                    resp.raise_for_status()
                    with open(tmp_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(64 * 1024):
                            f.write(chunk)
            return tmp_path
        except Exception:
            # cleanup on failure
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise

    async def _send_media_with_multipart_if_needed(self, msg, resource_url: str, media_type: str, caption: str):
        """Send media either by URL or by multipart upload if it exceeds Telegram URL size limit."""
        size = await self._get_remote_size(resource_url)
        logging.debug("Remote size for %s: %s", resource_url, size)
        if size is not None and size <= self.MAX_TELEGRAM_MULTIPART_SIZE:
            # small enough to send by URL
            try:
                if media_type == "video":
                    await msg.reply_video(resource_url, caption=caption, parse_mode=ParseMode.HTML)
                elif media_type == "gif":
                    await msg.reply_animation(resource_url, caption=caption, parse_mode=ParseMode.HTML)
                return
            except Exception:
                logging.exception("Failed to send media by URL, will try multipart upload fallback")

        # if size unknown or greater than limit, download and send as multipart
        tmp_path = None
        try:
            tmp_path = await self._download_to_tempfile(resource_url)
            logging.info("Downloaded remote media to temp file %s for multipart upload", tmp_path)

            # probe downloaded file for video streams to get width/height using ffmpeg.probe
            width = None
            height = None
            if media_type == "video":
                try:
                    probe = await asyncio.to_thread(ffmpeg.probe, tmp_path)
                    for stream in probe.get("streams", []):
                        if stream.get("codec_type") == "video":
                            if stream.get("width") is not None:
                                width = int(stream.get("width"))
                            if stream.get("height") is not None:
                                height = int(stream.get("height"))
                            break
                    logging.debug("Probed dimensions for %s -> width=%s height=%s", tmp_path, width, height)
                except Exception:
                    logging.exception("ffmpeg.probe failed for %s; uploading without dimensions", tmp_path)

            with open(tmp_path, "rb") as f:
                input_file = InputFile(f)
                await msg.reply_video(input_file, caption=caption, width=width, height=height, parse_mode=ParseMode.HTML)

        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    logging.exception("Failed to delete temp file %s", tmp_path)
