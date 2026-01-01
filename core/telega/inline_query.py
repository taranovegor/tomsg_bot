from urllib.parse import urlparse
import logging
import asyncio
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
    InlineQueryResultVideo,
    InlineQueryResultPhoto,
    InlineQueryResultGif,
    InlineQuery,
)
from telegram.constants import ParseMode

from core import Parser, InvalidUrlError, ParserNotFoundError
from core.analytics.analytics import Analytics, Events, Event
from core.files.exception import FileTooLarge
from core.files.validator import RemoteFileValidator
from core.parser.entity import Content, MediaType
from core.telega.renderer import MessageRenderer
from core.utils.htmls import strip_tags
from core.utils.uid import generate_uuid
from core.utils.urls import is_valid_url


class InlineQueryHandler:
    """
    Handle inline queries that contain URLs: parse, validate media, build results, and log.

    Responsibilities:
    - Validate query text as a URL and parse it into Content.
    - Validate remote media sizes and assemble InlineQueryResult items (media + fallback article).
    - Answer the inline query and record analytics events.

    Side effects: returns inline results to Telegram; may omit media that exceed limits.
    """

    MEDIA_LABELS = {
        MediaType.PHOTO.value: "фото",
        MediaType.VIDEO.value: "видео",
        MediaType.GIF.value: "GIF",
    }

    def __init__(
        self,
        parser: Parser,
        renderer: MessageRenderer,
        file_validator: RemoteFileValidator,
        analytics: Analytics,
    ):
        """
        Store parser, renderer, remote file validator and analytics references.
        """
        self.parser = parser
        self.renderer = renderer
        self.file_validator = file_validator
        self.analytics = analytics

    async def handle(self, update: Update, _) -> None:
        """
        Process an inline query: validate URL, parse content, and answer results or an error.

        Behavior notes:
        - Skips empty queries.
        - Returns a single error article on invalid URL, unsupported host, or exceptions.
        - Always logs page views and exceptions to analytics; method returns None.
        """
        inline_query = update.inline_query
        query = inline_query.query or ""
        if not query:
            logging.debug("Empty query received")
            return

        logging.debug("Received inline query: %s", query)

        events = Events(inline_query.from_user.id, "telegram", "inline")

        if not is_valid_url(query):
            logging.warning("Invalid URL received: %s", query)
            e = InvalidUrlError()
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
            )
            await self._send_error(
                inline_query,
                "invalid_url",
                "❌ Невозможно обработать",
                "Введенный текст не содержит корректной ссылки для обработки.",
            )
            await self.analytics.log(events)
            return

        hostname = urlparse(query).netloc
        try:
            logging.info("Processing valid URL from hostname: %s", hostname)
            events.add(Event("page_view").add("page_location", query))
            content = await asyncio.to_thread(self.parser.parse, query)
            logging.debug("Successfully parsed entity for query: %s", query)
            await self._send_content(inline_query, content)
        except ParserNotFoundError as e:
            logging.warning("Parser not found for hostname: %s", hostname)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
                .add("hostname", hostname)
            )
            await self._send_error(
                inline_query,
                "no_parser_found",
                "🔗 Ссылка не поддерживается",
                "К сожалению, ссылка с этого ресурса еще не поддерживается.",
            )
        except Exception as e:
            logging.error("Exception while processing query: %s", query, exc_info=True)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
            )
            await self._send_error(
                inline_query,
                "exception",
                "⚠️ Ошибка обработки",
                "Произошла ошибка при обработке вашего запроса. Повторите попытку позже.",
            )
        finally:
            await self.analytics.log(events)

    async def _send_content(self, inline_query: InlineQuery, content: Content) -> None:
        """
        Build and answer inline query results from parsed content.

        Key points:
        - Use renderer to create visible text and description.
        - Asynchronously validate remote media before including them.
        - Add a fallback Article that sends the rendered message text.
        - Answers the inline query (real-time, cache_time=0).
        """
        text = self.renderer.render(content)
        raw_text = strip_tags(text)

        results = []

        if content.media and len(content.media) > 0:
            result = None

            validate_tasks = [
                asyncio.create_task(self._validate_media(m)) for m in content.media
            ]
            allowed_flags = await asyncio.gather(*validate_tasks)

            allowed_media = [m for m, ok in zip(content.media, allowed_flags) if ok]

            for media in allowed_media:
                kwargs = {
                    "id": generate_uuid(),
                    "title": f"➡️ Отправить {self.MEDIA_LABELS[media.type()]}",
                    "caption": self.renderer.render_with_link(content),
                    "parse_mode": ParseMode.HTML,
                    "description": raw_text,
                }

                match media.type():
                    case MediaType.PHOTO:
                        result = InlineQueryResultPhoto(
                            photo_url=media.resource_url,
                            thumbnail_url=media.thumbnail_url or media.resource_url,
                            **kwargs,
                        )
                    case MediaType.GIF:
                        result = InlineQueryResultGif(
                            gif_url=media.resource_url,
                            thumbnail_url=media.thumbnail_url,
                            **kwargs,
                        )
                    case MediaType.VIDEO:
                        result = InlineQueryResultVideo(
                            video_url=media.resource_url,
                            mime_type=media.mime_type,
                            thumbnail_url=media.thumbnail_url,
                            **kwargs,
                        )
                    case _:
                        continue

                results.append(result)

        if content.text or 0 == len(results):
            results.insert(
                0,
                InlineQueryResultArticle(
                    id=generate_uuid(),
                    title="➡️ Отправить как сообщение",
                    description=raw_text,
                    input_message_content=InputTextMessageContent(
                        message_text=self.renderer.render_with_link(content),
                        parse_mode=ParseMode.HTML,
                        link_preview_options=LinkPreviewOptions(is_disabled=True),
                    ),
                ),
            )

        await inline_query.answer(results, cache_time=0)

    @staticmethod
    async def _send_error(
        inline_query: InlineQuery, identifier: str, title: str, description: str
    ) -> None:
        """
        Reply with a single error Article describing the failure.

        Purpose:
        - Provide a clear, user-facing result when processing cannot proceed.
        - The article includes the original query as message text and a short notice.
        """
        logging.debug("Generating error result: %s", identifier)
        await inline_query.answer(
            [
                InlineQueryResultArticle(
                    id=f"e_{identifier}",
                    title=title,
                    description=description,
                    input_message_content=InputTextMessageContent(
                        message_text=f"{inline_query.query}\n\n"
                        f"❗️Это сообщение введено пользователем, бот не отвечает за его содержание.",
                    ),
                ),
            ],
            cache_time=0,
        )

    async def _validate_media(self, media) -> bool:
        """
        Check if a remote media item is acceptable for inline results.

        Returns True if size checks pass; False for known oversize.
        On unexpected validation errors, returns True to avoid losing content.
        """
        try:
            await self.file_validator.validate_size(media.resource_url)
            return True
        except FileTooLarge:
            logging.info("Media skipped due to size limit: %s", media.resource_url)
            return False
        except Exception:
            logging.debug(
                "Validation error treated permissively for: %s",
                media.resource_url,
                exc_info=True,
            )
            return True
