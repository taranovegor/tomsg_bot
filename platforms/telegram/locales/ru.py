translations: dict[str, str] = {
    # message.py — reply texts
    "invalid_url_reply": "Введённый текст не является корректным URL.",
    "no_parser_reply": "Ссылка с этого ресурса ещё не поддерживается.",
    "exception_reply": "Произошла ошибка при обработке вашего запроса. Повторите попытку позже.",
    # inline_query.py — media labels
    "media_label_photo": "фото",
    "media_label_video": "видео",
    "media_label_gif": "GIF",
    # inline_query.py — send prefixes
    "send_media": "➡️ Отправить {type}",
    "send_as_message": "➡️ Отправить как сообщение",
    # inline_query.py — error titles
    "error_invalid_url_title": "❌ Невозможно обработать",
    "error_no_parser_title": "🔗 Ссылка не поддерживается",
    "error_exception_title": "⚠️ Ошибка обработки",
    # inline_query.py — error descriptions
    "error_invalid_url_desc": "Введенный текст не содержит корректной ссылки для обработки.",
    "error_no_parser_desc": "К сожалению, ссылка с этого ресурса еще не поддерживается.",
    "error_exception_desc": "Произошла ошибка при обработке вашего запроса. Повторите попытку позже.",  # noqa: E501
    # inline_query.py — disclaimer
    "disclaimer_user_content": "❗️Это сообщение введено пользователем, бот не отвечает за его содержание.",  # noqa: E501
}
