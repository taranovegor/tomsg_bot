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

from core import Parser, ParserNotFoundError
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
        if not query:
            return

        events = Events(update.inline_query.from_user.id)

        if self._is_valid_url(query):
            results = await self._handle_valid_url(query, events)
        else:
            results = self._handle_invalid_url(query, events)

        await update.inline_query.answer(results=results, cache_time=0)
        await self.analytics.log(events)

    def _is_valid_url(self, query: str) -> bool:
        """Checks if the query is a valid URL."""
        return validators.url(query) or self.URL_REGEX.match(query)

    async def _handle_valid_url(
        self, query: str, events: Events
    ) -> list[InlineQueryResult]:
        """Handles a valid URL query by parsing it and generating results."""
        domain = urlparse(query).netloc
        events.add(Event("query_received").add("domain", domain))
        try:
            entity = self.parser.parse(query)
            return self.results_factory.create(entity)
        except ParserNotFoundError:
            events.add(
                Event("error_handled")
                .add("type", "parser not found")
                .add("domain", domain)
            )
            return self._error_result(
                "no_parser_found",
                "🔗 Ссылка не поддерживается",
                "К сожалению, ссылка с этого ресурса еще не поддерживается.",
                query,
            )
        except Exception as e:
            events.add(Event("error_handled").add("type", str(e)))
            logging.error("An exception occurred: %s", e)
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
        events.add(Event("error_handled").add("type", "invalid_url"))
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
