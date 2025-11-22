from uuid import uuid4
from telegram import (
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InlineQueryResultPhoto,
    InlineQueryResultGif,
    InputTextMessageContent,
    LinkPreviewOptions
)
from telegram.constants import ParseMode
from .message_formatter import MessageFormatter


class InlineResultFactory:
    @staticmethod
    def _uid() -> str:
        return str(uuid4())

    @staticmethod
    def create(content):
        text = MessageFormatter.text(content)
        link = content.backlink

        results = [
            InlineQueryResultArticle(
                id=InlineResultFactory._uid(),
                title="➡️ Отправить как сообщение",
                description=text,
                input_message_content=InputTextMessageContent(
                    message_text=MessageFormatter.with_backlink(text, "📄", link),
                    parse_mode=ParseMode.HTML,
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                ),
            )
        ]

        for m in content.media or []:
            emoji = {"photo": "🖼", "video": "📺", "gif": "🎞️"}[m.type()]
            message = MessageFormatter.with_backlink(text, emoji, link)

            if m.type() == "photo":
                results.append(
                    InlineQueryResultPhoto(
                        id=InlineResultFactory._uid(),
                        photo_url=m.resource_url,
                        thumbnail_url=m.thumbnail_url or m.resource_url,
                        caption=message,
                        parse_mode=ParseMode.HTML,
                        description=text
                    )
                )
            elif m.type() == "video":
                results.append(
                    InlineQueryResultVideo(
                        id=InlineResultFactory._uid(),
                        video_url=m.resource_url,
                        mime_type=m.mime_type,
                        thumbnail_url=m.thumbnail_url,
                        caption=message,
                        parse_mode=ParseMode.HTML,
                        description=text
                    )
                )
            elif m.type() == "gif":
                results.append(
                    InlineQueryResultGif(
                        id=InlineResultFactory._uid(),
                        gif_url=m.resource_url,
                        thumbnail_url=m.thumbnail_url,
                        caption=message,
                        parse_mode=ParseMode.HTML,
                        description=text
                    )
                )
        return results
