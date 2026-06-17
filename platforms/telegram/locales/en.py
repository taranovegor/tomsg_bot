translations: dict[str, str] = {
    # message.py — reply texts
    "invalid_url_reply": "The entered text is not a valid URL.",
    "no_parser_reply": "Links from this resource are not yet supported.",
    "exception_reply": "An error occurred while processing your request. Please try again later.",
    # inline_query.py — media labels
    "media_label_photo": "Photo",
    "media_label_video": "Video",
    "media_label_gif": "GIF",
    # inline_query.py — send prefixes
    "send_media": "➡️ Send {type}",
    "send_as_message": "➡️ Send as message",
    # inline_query.py — error titles
    "error_invalid_url_title": "❌ Cannot process",
    "error_no_parser_title": "🔗 Link not supported",
    "error_exception_title": "⚠️ Processing error",
    # inline_query.py — error descriptions
    "error_invalid_url_desc": "The entered text does not contain a valid link for processing.",
    "error_no_parser_desc": "Unfortunately, links from this resource are not yet supported.",
    "error_exception_desc": "An error occurred while processing your request. Please try again later.",  # noqa: E501
    # inline_query.py — disclaimer
    "disclaimer_user_content": "❗️This message was entered by the user; the bot is not responsible for its content.",  # noqa: E501
}
