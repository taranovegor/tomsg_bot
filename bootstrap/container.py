import hashlib
import logging
import os
import tempfile
from pathlib import Path

from core.files.downloader import MediaDownloader
from core.files.resolver import FileResolver
from core.files.storage import LocalStorage
from core.files.validator import RemoteFileValidator
from core.media.processor import VideoProcessor
from core.telega.renderer import MessageRenderer
from parser import (
    cmtt,
    habr,
    instagram,
    reddit,
    redspecial,
    tiktok,
    trashbox,
    truthsocial,
    tumblr,
    twitter,
    vk,
    youtube,
)

from telegram.ext import Application, InlineQueryHandler, MessageHandler, filters

from bootstrap import meta
from core.parser import Parser
from core.analytics.analytics import Analytics
from core.analytics.ga import GoogleAnalytics
from core.config import Config
from core.parser import DelegatingParser
from core.telega.message import MessageHandler as TelegaMessageHandler
from core.telega.inline_query import InlineQueryHandler as TelegaInlineQueryHandler


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
        try:
            logging.debug("Initializing service instance")
            self.instance = self.initializer(container)
            self.initialized = True
            logging.info("Service initialized successfully")
        except Exception as e:
            logging.error("Error initializing service", exc_info=True)
            raise RuntimeError(f"Service initialization failed: {e}") from e


def _tempdir(_: Container) -> tempfile.TemporaryDirectory:
    """Creates and returns a temporary directory path."""
    tempdir = tempfile.TemporaryDirectory()
    logging.info("Created temporary directory at %s", tempdir.name)
    return tempdir


def __analytics_ga(container: Container) -> Analytics:
    """Initializes and returns a GoogleAnalytics instance."""
    config = container.config.google_analytics
    return GoogleAnalytics(
        config.measurement_id,
        config.secret,
        f"{os.name}:{meta.name()}:{meta.version()}",
        lambda x: hashlib.sha256(
            (str(x) + config.user_identifier_salt).encode()
        ).hexdigest(),
    )


def _files_media_downloader(_: Container) -> MediaDownloader:
    """MediaDownloader instance with a 2 GiB streaming cap and 5-minute timeout."""
    return MediaDownloader(
        f"{os.name}:{meta.name()}:{meta.version()} (like TwitterBot)",
        timeout=300,
        max_bytes=2 * 1024 * 1024 * 1024,
    )


def _files_file_resolver(container: Container) -> FileResolver:
    """FileResolver created using an inline RemoteFileValidator (not registered as a service)."""
    validator = RemoteFileValidator(
        f"{os.name}:{meta.name()}:{meta.version()} (like TwitterBot)",
        2 * 1024 * 1024 * 1024,
    )
    return FileResolver(
        validator,
        container.get("files__media_downloader"),
        container.get("files__local_storage_files"),
    )


def _files_local_storage_files(container: Container) -> LocalStorage:
    """Storage for downloaded files."""
    return LocalStorage(Path(container.get("tempdir").name))


def _media_video_processor(container: Container) -> VideoProcessor:
    """Video processor with its own storage."""
    return VideoProcessor(container.get("files__local_storage_files"))


def __parser_delegating_parser(container: Container) -> Parser:
    """Initializes and returns a DelegatingParser instance."""
    return DelegatingParser(
        [
            container.get("parser__cmtt"),
            container.get("parser__habr"),
            container.get("parser__instagram"),
            container.get("parser__reddit"),
            container.get("parser_redspecial"),
            container.get("parser__tiktok"),
            container.get("parser__trashbox"),
            container.get("parser__truthsocial"),
            container.get("parser__tumblr"),
            container.get("parser__twitter"),
            container.get("parser__vk"),
            container.get("parser__youtube"),
        ]
    )


def __app(container: Container) -> None:
    """Initializes and runs the Telegram bot application."""
    logging.info("Initializing Telegram bot application")
    builder = Application.builder()
    builder.token(container.config.telegram.bot_token)
    if container.config.telegram.base_url:
        logging.info(
            f"Using custom Telegram API base URL: {container.config.telegram.base_url}"
        )
        builder.base_url(container.config.telegram.base_url)
    application = builder.build()

    application.add_handler(
        InlineQueryHandler(container.get("telega__inline_query_handler").handle)
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE,
            container.get("telega__message_handler").handle,
        )
    )

    logging.info("Starting Telegram bot polling")

    return application.run_polling()


def __parser_cmtt(container: Container) -> Parser:
    """Initializes and returns a cmtt.Parser instance."""
    return cmtt.Parser(
        f"{os.name}:{meta.name()}:{meta.version()}",
        timeout=container.config.parser_http_timeout,
    )


def __parser_habr(container: Container) -> Parser:
    """Initializes and returns a habr.Parser instance."""
    return habr.Parser(
        f"{os.name}:{meta.name()}:{meta.version()}",
        timeout=container.config.parser_http_timeout,
    )


def __parser_instagram(container: Container) -> Parser:
    """Initializes and returns an instagram.Parser instance."""
    config = container.config.instagram

    cipher = instagram.Cipher(config.encryption_key)

    return instagram.Parser(
        config.parser_url,
        f"{os.name}:{meta.name()}:{meta.version()} (like TwitterBot)",
        cipher,
        timeout=container.config.parser_http_timeout,
    )


def __parser_reddit(container: Container) -> Parser:
    """Initializes and returns a reddit.Parser instance."""
    config = container.config.reddit
    return reddit.Parser(
        config.client_id,
        config.client_secret,
        f"{os.name}:{meta.name()}:{meta.version()} (by /u/{config.app_owner_username})",
        timeout=container.config.parser_http_timeout,
    )


def __parser_redspecial(container: Container) -> Parser:
    """Initializes and returns a redspecial.Parser instance."""
    return redspecial.Parser(
        f"{os.name}:{meta.name()}:{meta.version()}",
        timeout=container.config.parser_http_timeout,
    )


def __parser_tiktok(container: Container) -> Parser:
    """Initializes and returns a tiktok.Parser instance."""
    config = container.config.tiktok
    return tiktok.Parser(
        config.video_resource_url,
        config.thumbnail_resource_url,
        f"{os.name}:{meta.name()}:{meta.version()}",
        timeout=container.config.parser_http_timeout,
    )


def __parser_trashbox(container: Container) -> Parser:
    """Initializes and returns a trashbox.Parser instance."""
    return trashbox.Parser(
        f"{os.name}:{meta.name()}:{meta.version()}",
        timeout=container.config.parser_http_timeout,
    )


def __parser_truthsocial(container: Container) -> Parser:
    """Initializes and returns a truthsocial.Parser instance."""
    return truthsocial.Parser(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 tomsg_bot",
        timeout=container.config.parser_http_timeout,
    )


def __parser_tumblr(container: Container) -> Parser:
    """Initializes and returns a tumblr.Parser instance."""
    config = container.config.tumblr
    return tumblr.Parser(
        config.api_key,
        f"{os.name}:{meta.name()}:{meta.version()} TelegramBot (like TwitterBot)",
        timeout=container.config.parser_http_timeout,
    )


def __parser_twitter(container: Container) -> Parser:
    """Initializes and returns a twitter.Parser instance."""
    return twitter.Parser(
        f"{os.name}:{meta.name()}:{meta.version()} TelegramBot (like TwitterBot)",
        timeout=container.config.parser_http_timeout,
    )


def __parser_vk(container: Container) -> Parser:
    """Initializes and returns a vk.Parser instance."""
    config = container.config.vk
    return vk.Parser(
        config.thumbnail_url,
        f"{os.name}:{meta.name()}:{meta.version()} TelegramBot (like TwitterBot)",
        timeout=container.config.parser_http_timeout,
    )


def _parser_youtube(container: Container) -> Parser:
    """Initializes and returns a youtube.Parser instance."""
    config = container.config.youtube
    return youtube.Parser(
        config.api_key,
        f"{os.name}:{meta.name()}:{meta.version()} TelegramBot (like TwitterBot)",
        timeout=container.config.parser_http_timeout,
    )


def _telega_inline_query_handler(container: Container) -> TelegaInlineQueryHandler:
    """TelegaInlineQueryHandler constructed from container services; validator created inline."""
    validator = RemoteFileValidator(
        f"{os.name}:{meta.name()}:{meta.version()} (like TwitterBot)",
        20 * 1024 * 1024,
    )
    return TelegaInlineQueryHandler(
        container.get("parser_delegating_parser"),
        container.get("telega__message_renderer"),
        validator,
        container.get("analytics_ga"),
    )


def _telega_message_handler(container: Container) -> TelegaMessageHandler:
    """TelegaMessageHandler constructed from container services."""
    return TelegaMessageHandler(
        container.get("parser_delegating_parser"),
        container.get("telega__message_renderer"),
        container.get("files__file_resolver"),
        container.get("media__video_processor"),
        container.get("analytics_ga"),
    )


def _telega_message_renderer(_: Container) -> MessageRenderer:
    """Shared MessageRenderer instance."""
    return MessageRenderer()


def load_container(config):
    """Loads the container with the provided configuration and registers services."""
    logging.info("Loading container with services")
    container = Container(config)

    container.register("tempdir", _tempdir)

    container.register("analytics_ga", __analytics_ga)

    container.register("files__media_downloader", _files_media_downloader)
    container.register("files__file_resolver", _files_file_resolver)
    container.register("files__local_storage_files", _files_local_storage_files)

    container.register("media__video_processor", _media_video_processor)

    container.register("parser_delegating_parser", __parser_delegating_parser)
    container.register("parser__cmtt", __parser_cmtt)
    container.register("parser__habr", __parser_habr)
    container.register("parser__instagram", __parser_instagram)
    container.register("parser__reddit", __parser_reddit)
    container.register("parser_redspecial", __parser_redspecial)
    container.register("parser__tiktok", __parser_tiktok)
    container.register("parser__trashbox", __parser_trashbox)
    container.register("parser__truthsocial", __parser_truthsocial)
    container.register("parser__tumblr", __parser_tumblr)
    container.register("parser__twitter", __parser_twitter)
    container.register("parser__vk", __parser_vk)
    container.register("parser__youtube", _parser_youtube)

    container.register("telega__inline_query_handler", _telega_inline_query_handler)
    container.register("telega__message_handler", _telega_message_handler)
    container.register("telega__message_renderer", _telega_message_renderer)

    container.register("app", __app)

    logging.info("Container loaded successfully")

    return container
