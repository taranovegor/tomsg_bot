"""Service key constants — single source of truth for DI container keys.

Convention: category_subject (lowercase, single underscore).
Parser keys are auto-generated as ``parser_{name}`` from the registry.
"""

# Infrastructure
TEMPDIR = "tempdir"
ANALYTICS = "analytics"
FILES_MEDIA_DOWNLOADER = "files_media_downloader"
FILES_FILE_RESOLVER = "files_file_resolver"
FILES_LOCAL_STORAGE = "files_local_storage"
FILES_DOWNLOAD_VALIDATOR = "files_download_validator"
FILES_INLINE_VALIDATOR = "files_inline_validator"
MEDIA_VIDEO_PROCESSOR = "media_video_processor"

# Parsers
PARSER_DELEGATING = "parser_delegating"
PARSER_TEMPLATE = "parser_{}"

# Pipeline
PIPELINE = "pipeline"

# Telegram
TELEGA_INLINE_QUERY_HANDLER = "telega_inline_query_handler"
TELEGA_DELIVERY = "telega_delivery"
TELEGA_MESSAGE_HANDLER = "telega_message_handler"
TELEGA_MESSAGE_RENDERER = "telega_message_renderer"

# App
APP = "app"
