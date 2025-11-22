import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode

from .base_handler import BaseHandler
from core.telega.url_utils import UrlUtils
from core.telega.result_factory import InlineResultFactory
from core import ParserNotFoundError, InvalidUrlError
from core.analytics.analytics import Events

class InlineHandler(BaseHandler):
    def __init__(self, parser, analytics):
        super().__init__(parser, analytics)
        self.factory = InlineResultFactory()

    async def handle(self, update, _):
        query = update.inline_query.query.strip()
        user = update.inline_query.from_user.id
        events = Events(user)

        if not UrlUtils.is_valid_url(query):
            await update.inline_query.answer(
                results=[InlineQueryResultArticle(
                    id="invalid",
                    title="❌ Невозможно обработать",
                    description="Некорректный URL",
                    input_message_content=InputTextMessageContent(
                        f"{query}\n\n❗️Это сообщение введено пользователем.",
                        parse_mode=ParseMode.HTML
                    )
                )],
                cache_time=0
            )
            await self.analytics.log(events)
            return

        try:
            entity = await self.process_url(query, events)
            results = self.factory.create(entity)
        except ParserNotFoundError:
            results = [InlineQueryResultArticle(
                id="notfound",
                title="🔗 Ссылка не поддерживается",
                description="Источник не поддерживается",
                input_message_content=InputTextMessageContent(
                    f"{query}\n\n❗️Это сообщение введено пользователем.",
                    parse_mode=ParseMode.HTML
                )
            )]
        except Exception as e:
            logging.exception(e)
            results = [InlineQueryResultArticle(
                id="error",
                title="⚠️ Ошибка обработки",
                description="Попробуйте позже",
                input_message_content=InputTextMessageContent(
                    "⚠️ Ошибка обработки",
                    parse_mode=ParseMode.HTML
                )
            )]

        await update.inline_query.answer(results=results, cache_time=0)
        await self.analytics.log(events)
