import hashlib
import logging
import os
import tempfile
from pathlib import Path

from telegram.ext import Application, InlineQueryHandler, MessageHandler, filters

from bootstrap import keys
from core.config import Config
from core.pipeline import Pipeline
from core.ports import DelegatingParser, Parser
from infra.analytics.analytics import Analytics
from infra.analytics.ga import GoogleAnalytics
from infra.files.downloader import MediaDownloader
from infra.files.resolver import FileResolver
from infra.files.storage import LocalStorage
from infra.files.validator import RemoteFileValidator
from infra.media.processor import VideoProcessor
from platforms.telegram import DOWNLOAD_FILE_SIZE_LIMIT, INLINE_FILE_SIZE_LIMIT
from platforms.telegram.inline_query import (
    InlineQueryHandler as TelegaInlineQueryHandler,
)
from platforms.telegram.message import (
    MessageHandler as TelegaMessageHandler,
)
from platforms.telegram.message import (
    TelegramDelivery as TelegaDelivery,
)
from platforms.telegram.renderer import MessageRenderer
from shared import info


class Container:
    """A class representing a container for managing services and their initialization."""

    def __init__(self, config: Config):
        """Initializes the container with a given configuration."""
        self.config = config
        self.__services = {}

    def get(self, name):
        """Fetches a service by its name and initializes it if not already initialized."""
        logging.debug("Fetching service: %s", name)
        service = self.__services.get(name)
        if not service:
            logging.error("Service not defined: %s", name)
            raise KeyError(f"Service not defined: {name}")
        if not service.initialized:
            logging.info("Initializing service: %s", name)
            try:
                service.initialize(self)
                logging.info("Service %s initialized successfully", name)
            except Exception as e:
                logging.critical("Failed to initialize service %s", name, exc_info=True)
                raise RuntimeError(f"Service initialization error for {name}") from e
        return service.instance

    def register(self, name, initializer):
        """Registers a service by name with its initializer."""
        if name in self.__services:
            logging.warning("Service %s is already registered. Overwriting.", name)
        logging.debug("Registering service: %s", name)
        self.__services[name] = Service(initializer)


class Service:
    """A class that represents a service with an initializer and instance."""

    def __init__(self, initializer):
        """Initializes the service with the given initializer."""
        self.initializer = initializer
        self.initialized = False
        self.instance = None

    def initialize(self, container: Container):
        """Initializes the service and sets its instance."""
        logging.debug("Initializing service instance")
        self.instance = self.initializer(container)
        self.initialized = True
        logging.info("Service initialized successfully")


def _tempdir(_: Container) -> tempfile.TemporaryDirectory:
    """Creates and returns a temporary directory path."""
    tempdir = tempfile.TemporaryDirectory()
    logging.info("Created temporary directory at %s", tempdir.name)
    return tempdir


def _analytics(container: Container) -> Analytics:
    """Initializes and returns a GoogleAnalytics instance."""
    config = container.config.google_analytics
    return GoogleAnalytics(
        config.measurement_id,
        config.secret,
        f"{os.name}:{info.name()}:{info.version()}",
        lambda x: hashlib.sha256((str(x) + config.user_identifier_salt).encode()).hexdigest(),
    )


def _files_media_downloader(_: Container) -> MediaDownloader:
    """MediaDownloader with per-platform streaming cap and timeout."""
    return MediaDownloader(
        f"{os.name}:{info.name()}:{info.version()} (like TwitterBot)",
        timeout=300,
        max_bytes=DOWNLOAD_FILE_SIZE_LIMIT,
    )


def _files_download_validator(_: Container) -> RemoteFileValidator:
    """RemoteFileValidator for full-size downloads (2 GB limit)."""
    return RemoteFileValidator(
        f"{os.name}:{info.name()}:{info.version()} (like TwitterBot)",
        DOWNLOAD_FILE_SIZE_LIMIT,
    )


def _files_inline_validator(_: Container) -> RemoteFileValidator:
    """RemoteFileValidator for inline-query downloads (20 MB limit)."""
    return RemoteFileValidator(
        f"{os.name}:{info.name()}:{info.version()} (like TwitterBot)",
        INLINE_FILE_SIZE_LIMIT,
    )


def _files_file_resolver(container: Container) -> FileResolver:
    """FileResolver with per-platform size limit."""
    return FileResolver(
        container.get(keys.FILES_DOWNLOAD_VALIDATOR),
        container.get(keys.FILES_MEDIA_DOWNLOADER),
        container.get(keys.FILES_LOCAL_STORAGE),
    )


def _files_local_storage(container: Container) -> LocalStorage:
    """Storage for downloaded files."""
    return LocalStorage(Path(container.get(keys.TEMPDIR).name))


def _media_video_processor(container: Container) -> VideoProcessor:
    """Video processor with its own storage."""
    return VideoProcessor(container.get(keys.FILES_LOCAL_STORAGE))


def _parser_delegating(container: Container) -> Parser:
    """Initializes and returns a DelegatingParser with all registered parsers."""
    import parsers

    factories = parsers.registry.get_factories()
    return DelegatingParser(
        [container.get(keys.PARSER_TEMPLATE.format(name)) for name in sorted(factories)]
    )


def _app(container: Container) -> None:
    """Initializes and runs the Telegram bot application."""
    logging.info("Initializing Telegram bot application")
    builder = Application.builder()
    builder.token(container.config.telegram.bot_token)
    if container.config.telegram.base_url:
        logging.info(f"Using custom Telegram API base URL: {container.config.telegram.base_url}")
        builder.base_url(container.config.telegram.base_url)
    application = builder.build()

    application.add_handler(
        InlineQueryHandler(container.get(keys.TELEGA_INLINE_QUERY_HANDLER).handle)
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE,
            container.get(keys.TELEGA_MESSAGE_HANDLER).handle,
        )
    )

    logging.info("Starting Telegram bot polling")

    return application.run_polling()


def _telega_inline_query_handler(
    container: Container,
) -> TelegaInlineQueryHandler:
    """TelegaInlineQueryHandler constructed from container services."""
    return TelegaInlineQueryHandler(
        container.get(keys.PARSER_DELEGATING),
        container.get(keys.TELEGA_MESSAGE_RENDERER),
        container.get(keys.FILES_INLINE_VALIDATOR),
        container.get(keys.ANALYTICS),
    )


def _pipeline(container: Container) -> Pipeline:
    """Neutral content pipeline shared by all platforms."""
    return Pipeline(
        container.get(keys.PARSER_DELEGATING),
        container.get(keys.FILES_FILE_RESOLVER),
        container.get(keys.MEDIA_VIDEO_PROCESSOR),
    )


def _telega_delivery(container: Container) -> TelegaDelivery:
    """Telegram-specific delivery using shared renderer."""
    return TelegaDelivery(container.get(keys.TELEGA_MESSAGE_RENDERER))


def _telega_message_handler(container: Container) -> TelegaMessageHandler:
    """TelegaMessageHandler constructed from container services."""
    return TelegaMessageHandler(
        container.get(keys.PIPELINE),
        container.get(keys.TELEGA_DELIVERY),
        container.get(keys.ANALYTICS),
    )


def _telega_message_renderer(_: Container) -> MessageRenderer:
    """Shared MessageRenderer instance."""
    return MessageRenderer()


def load_container(config):
    """Loads the container with the provided configuration and registers services."""
    logging.info("Loading container with services")
    container = Container(config)

    container.register(keys.TEMPDIR, _tempdir)
    container.register(keys.ANALYTICS, _analytics)
    container.register(keys.FILES_MEDIA_DOWNLOADER, _files_media_downloader)
    container.register(keys.FILES_DOWNLOAD_VALIDATOR, _files_download_validator)
    container.register(keys.FILES_INLINE_VALIDATOR, _files_inline_validator)
    container.register(keys.FILES_FILE_RESOLVER, _files_file_resolver)
    container.register(keys.FILES_LOCAL_STORAGE, _files_local_storage)
    container.register(keys.MEDIA_VIDEO_PROCESSOR, _media_video_processor)
    container.register(keys.PIPELINE, _pipeline)
    container.register(keys.PARSER_DELEGATING, _parser_delegating)

    import parsers

    factories = parsers.registry.get_factories()
    for name in sorted(factories):
        container.register(keys.PARSER_TEMPLATE.format(name), factories[name])

    container.register(keys.TELEGA_INLINE_QUERY_HANDLER, _telega_inline_query_handler)
    container.register(keys.TELEGA_DELIVERY, _telega_delivery)
    container.register(keys.TELEGA_MESSAGE_HANDLER, _telega_message_handler)
    container.register(keys.TELEGA_MESSAGE_RENDERER, _telega_message_renderer)
    container.register(keys.APP, _app)

    logging.info("Container loaded successfully")

    return container
