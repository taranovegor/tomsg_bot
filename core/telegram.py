import logging
import re
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import validators
from telegram import (
    InlineQueryResult,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
    Update,
    InlineQueryResultVideo,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from core.analytics import Analytics, Event, Events
from core.parser import Entity, NoParserFound, Parser, Text, Video


class ErrFactoryNotFound(Exception):
    pass


class ResultFactory(ABC):
    @abstractmethod
    def create(self, e: Entity) -> InlineQueryResult:
        pass


class DelegatingResultFactory(ResultFactory):
    def __init__(self, factories: dict[str, ResultFactory]):
        self.factories = factories

    def create(self, e: Entity) -> InlineQueryResult:
        if e.type() not in self.factories:
            raise ErrFactoryNotFound
        return self.factories[e.type()].create(e)


class TextFactory(ResultFactory):
    def create(self, e: Text) -> InlineQueryResult:
        msg = '💁' if e.author else ''
        if e.author.url == '':
            msg += e.author.text
        elif e.author.text == '':
            msg += f'<a href="{e.author.url}">{e.author.url}</a>'
        else:
            msg += f'<a href="{e.author.url}">{e.author.text}</a>'
        msg += ', '
        msg += e.created_at.strftime('%d.%m.%y %H:%M %Z')
        msg += '\n'
        msg += e.content
        msg += '\n\n'
        if len(e.metrics) > 0:
            msg += ' '.join(e.metrics)
            msg += '\n\n'
        msg += '📄'
        if e.backlink.text == '':
            msg += f'<a href="{e.backlink.url}">{e.backlink.url}</a>'
        else:
            msg += f'<a href="{e.backlink.url}">{e.backlink.text}</a>'

        return InlineQueryResultArticle(
            id=e.type(),
            title='➡️ Отправить как сообщение',
            description=e.content,
            input_message_content=InputTextMessageContent(
                message_text=msg,
                parse_mode=ParseMode.HTML,
                link_preview_options=LinkPreviewOptions(
                    is_disabled=True,
                ),
            ),
        )


class VideoFactory(ResultFactory):
    def create(self, e: Video) -> InlineQueryResult:
        caption = '📹'
        if e.backlink.text == '':
            description = e.backlink.url
            caption += f'<a href="{e.backlink.url}">{e.backlink.url}</a>'
        else:
            description = e.backlink.text
            caption += f'<a href="{e.backlink.url}">{e.backlink.text}</a>'

        return InlineQueryResultVideo(
            id=e.type(),
            video_url=e.resource_url,
            mime_type=e.mime_type,
            thumbnail_url=e.thumbnail_url,
            title='➡️ Отправить видео',
            caption=caption,
            description=description,
            parse_mode=ParseMode.HTML,
        )


def error_result(identifier: str, title: str, description: str, query: str) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=f'e_{identifier}',
        title=title,
        description=description,
        input_message_content=InputTextMessageContent(
            message_text=f'{query}\n\n❗️Это сообщение введено пользователем, бот не отвечает за его содержание.',
        ),
    )


class Handler:
    URL_REGEX = re.compile(r"^(https?://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(/\S*)?$")

    def __init__(self, parser: Parser, result_factory: ResultFactory, analytics: Analytics):
        self.parser = parser
        self.result_factory = result_factory
        self.analytics = analytics

    async def inline_query(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        inline_query = update.inline_query
        query = inline_query.query
        if not query:
            return

        events = Events(str(inline_query.from_user.id))

        if validators.url(query) or self.URL_REGEX.match(query):
            domain = urlparse(query).netloc
            events.add(Event('query_received').add('domain', domain))
            try:
                entity = self.parser.parse(query)
                result = self.result_factory.create(entity)
            except NoParserFound:
                events.add(Event('error_handled').add('type', 'parser not found').add('domain', domain))
                result = error_result(
                    'no_parser_found',
                    '🔗 Ссылка не поддерживается',
                    'К сожалению, ссылка с этого ресурса еще не поддерживается.',
                    query,
                )
            except Exception as e:
                events.add(Event('error_handled').add('type', e))
                logging.error('An exception occurred: %s', e)
                result = error_result(
                    'exception',
                    '⚠️ Ошибка обработки',
                    'Произошла ошибка при обработке вашего запроса. Повторите попытку позже.',
                    query,
                )
        else:
            events.add(Event('error_handled').add('type', 'invalid_url'))
            result = error_result(
                'invalid_url',
                '❌ Невозможно обработать',
                'Введенный текст не содержит корректной ссылки для обработки.',
                query,
            )

        await update.inline_query.answer(results=[result], cache_time=1)
        await self.analytics.log(events)
