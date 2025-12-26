import logging
import re
from urllib.parse import urlparse

import validators
from telegram import (
    Update,
    InlineQueryResult,
    InputTextMessageContent,
    InlineQueryResultArticle,
)

from core import Parser, InvalidUrlError, ParserNotFoundError
from core.analytics.analytics import Analytics, Events, Event
from core.telega.inline import InlineResultsFactory


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
            return await self.results_factory.create(entity)
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
