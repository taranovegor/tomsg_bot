import logging
import os

from parser import (
    cmtt,
    habr,
    instagram,
    reddit,
    tiktok,
    trashbox,
    twitter,
    vk,
)

from telegram import Update
from telegram.ext import Application, InlineQueryHandler

from core import app
from core import Parser
from core.analytics.analytics import Analytics
from core.analytics.ga import GoogleAnalytics
from core.config import Config
from core.parser.parser import DelegatingParser
from core.telega.handler import InlineHandler
from core.telega.inline import InlineResultsFactory


class Container:
    """A class representing a container for managing services and their initialization."""

    def __init__(self, config: Config):
        """Initializes the container with a given configuration."""
        self.config = config
        self.__services = {}

    def get(self, name):
        """Fetches a service by its name and initializes it if not already initialized."""
        service = self.__services.get(name)
        if not service:
            logging.error("Service not defined: %s", name)
            raise KeyError(f"Service not defined: {name}")
        if not service.initialized:
            try:
                service.initialize(self)
            except Exception as e:
                logging.exception("Failed to initialize service %s", name)
                raise RuntimeError(f"Service initialization error for {name}") from e
        return service.instance

    def register(self, name, initializer):
        """Registers a service by name with its initializer."""
        if name in self.__services:
            logging.warning("Service %s is already registered. Overwriting.", name)
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
            self.instance = self.initializer(container)
            self.initialized = True
        except Exception as e:
            logging.exception("Error initializing service")
            raise RuntimeError(f"Service initialization failed: {e}") from e


def __analytics_ga(container: Container) -> Analytics:
    """Initializes and returns a GoogleAnalytics instance."""
    config = container.config.google_analytics
    return GoogleAnalytics(
        config.measurement_id,
        config.secret,
        f"{os.name}:{app.name()}:{app.version()}",
    )


def __parser_delegating_parser(container: Container) -> Parser:
    """Initializes and returns a DelegatingParser instance."""
    return DelegatingParser(
        [
            container.get("parser__cmtt"),
            container.get("parser__habr"),
            container.get("parser__instagram"),
            container.get("parser__reddit"),
            container.get("parser__tiktok"),
            container.get("parser__trashbox"),
            container.get("parser__twitter"),
            container.get("parser__vk"),
        ]
    )


def __telega_inline_results_factory(_: Container) -> InlineResultsFactory:
    """Initializes and returns an InlineResultsFactory instance."""
    return InlineResultsFactory()


def __telegra_inline_handler(container: Container) -> InlineHandler:
    """Initializes and returns an InlineHandler instance."""
    return InlineHandler(
        container.get("parser_delegating_parser"),
        container.get("telega_inline_results_factory"),
        container.get("analytics_ga"),
    )


def __app(container: Container) -> None:
    """Initializes and runs the Telegram bot application."""
    application = (
        Application.builder().token(container.config.telegram.bot_token).build()
    )
    application.add_handler(
        InlineQueryHandler(container.get("telega_inline_handler").inline_query)
    )
    return application.run_polling(allowed_updates=Update.INLINE_QUERY)


def __parser_cmtt(_: Container) -> Parser:
    """Initializes and returns a cmtt.Parser instance."""
    return cmtt.Parser(f"{os.name}:{app.name()}:{app.version()}")


def __parser_habr(_: Container) -> Parser:
    """Initializes and returns a habr.Parser instance."""
    return habr.Parser(f"{os.name}:{app.name()}:{app.version()}")


def __parser_instagram(container: Container) -> Parser:
    """Initializes and returns an instagram.Parser instance."""
    config = container.config.instagram
    return instagram.Parser(
        config.video_meta_url,
        config.video_storage_url,
        config.thumbnail_url,
        f"{os.name}:{app.name()}:{app.version()} (like TwitterBot)",
    )


def __parser_reddit(container: Container) -> Parser:
    """Initializes and returns a reddit.Parser instance."""
    config = container.config.reddit
    return reddit.Parser(
        config.client_id,
        config.client_secret,
        f"{os.name}:{app.name()}:{app.version()} (by /u/{config.app_owner_username})",
    )


def __parser_tiktok(container: Container) -> Parser:
    """Initializes and returns a tiktok.Parser instance."""
    config = container.config.tiktok
    return tiktok.Parser(
        config.video_resource_url,
        config.thumbnail_resource_url,
        f"{os.name}:{app.name()}:{app.version()}",
    )


def __parser_trashbox(_: Container) -> Parser:
    """Initializes and returns a trashbox.Parser instance."""
    return trashbox.Parser(f"{os.name}:{app.name()}:{app.version()}")


def __parser_twitter(container: Container) -> Parser:
    """Initializes and returns a twitter.Parser instance."""
    config = container.config.twitter
    return twitter.Parser(
        config.video_meta_url,
        f"{os.name}:{app.name()}:{app.version()} TelegramBot (like TwitterBot)",
    )


def __parser_vk(container: Container) -> Parser:
    """Initializes and returns a vk.Parser instance."""
    config = container.config.vk
    return vk.Parser(
        config.thumbnail_url,
        f"{os.name}:{app.name()}:{app.version()} TelegramBot (like TwitterBot)",
    )


def load_container(config):
    """Loads the container with the provided configuration and registers services."""
    container = Container(config)

    container.register("analytics_ga", __analytics_ga)
    container.register("parser_delegating_parser", __parser_delegating_parser)
    container.register("telega_inline_results_factory", __telega_inline_results_factory)
    container.register("telega_inline_handler", __telegra_inline_handler)
    container.register("app", __app)

    container.register("parser__cmtt", __parser_cmtt)
    container.register("parser__habr", __parser_habr)
    container.register("parser__instagram", __parser_instagram)
    container.register("parser__reddit", __parser_reddit)
    container.register("parser__tiktok", __parser_tiktok)
    container.register("parser__trashbox", __parser_trashbox)
    container.register("parser__twitter", __parser_twitter)
    container.register("parser__vk", __parser_vk)

    return container
