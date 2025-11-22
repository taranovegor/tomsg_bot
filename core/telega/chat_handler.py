import logging
from telegram.constants import ParseMode

from .base_handler import BaseHandler
from core.telega.url_utils import UrlUtils
from core.telega.message_formatter import MessageFormatter
from core.telega.media_sender import MediaSender
from core import ParserNotFoundError, InvalidUrlError
from core.analytics.analytics import Events, Event


class ChatHandler(BaseHandler):
    def __init__(self, parser, analytics):
        super().__init__(parser, analytics)

    async def handle(self, update, context):
        msg = update.message
        if not msg or not msg.text:
            return

        text = msg.text.strip()
        url = UrlUtils.extract_url(text)
        user_id = msg.from_user.id
        events = Events(user_id)

        # No URL
        if not url:
            events.add(Event("exception").add("type", InvalidUrlError.__name__))
            if msg.chat.type in ("group", "supergroup", "channel"):
                await self.analytics.log(events)
                return

            await msg.reply_text(
                f"{text}\n\n❗️Это сообщение введено пользователем.",
            )
            await self.analytics.log(events)
            return

        try:
            entity = await self.process_url(url, events)
        except ParserNotFoundError:
            await msg.reply_text("🔗 Ссылка не поддерживается")
            await self.analytics.log(events)
            return
        except Exception:
            logging.exception("Error while parsing URL")
            await msg.reply_text("⚠️ Ошибка обработки\nПопробуйте позже.")
            await self.analytics.log(events)
            return

        body = MessageFormatter.text(entity)
        backlink = entity.backlink
        main_message = MessageFormatter.with_backlink(body, "📄", backlink)

        # Send main text
        await msg.reply_text(main_message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        if not getattr(entity, "media", None):
            await self.analytics.log(events)
            return

        for m in entity.media:
            emoji = {"photo": "🖼", "video": "📺", "gif": "🎞️"}.get(m.type(), "")
            caption = MessageFormatter.with_backlink(body, emoji, backlink)
            await MediaSender.send(msg, m.resource_url, m.type(), caption)

        await self.analytics.log(events)
