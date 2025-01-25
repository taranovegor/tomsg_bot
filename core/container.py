import logging
import os

from telegram import Update
from telegram.ext import Application, InlineQueryHandler

from core import parser, telegram, app
from core.config import Config
from parser import (
    habr,
    reddit,
    trashbox,
)


class Container:
    def __init__(self, config: Config):
        self.config = config
        self.__services = {}

    def get(self, name):
        service = self.__services.get(name)
        if not service:
            logging.error("Service not defined: %s", name)
            raise KeyError(f"Service not defined: {name}")

        if not service.initialized:
            try:
                service.initialize(self)
            except Exception as e:
                logging.exception("Failed to initialize service '%s'", name)
                raise RuntimeError(f"Service initialization error for '{name}'") from e

        return service.instance

    def register(self, name, initializer):
        if name in self.__services:
            logging.warning("Service '%s' is already registered. Overwriting.", name)
        self.__services[name] = Service(initializer)


class Service:
    def __init__(self, initializer):
        self.initializer = initializer
        self.initialized = False
        self.instance = None

    def initialize(self, container: Container):
        try:
            self.instance = self.initializer(container)
            self.initialized = True
        except Exception as e:
            logging.exception("Error initializing service")
            raise RuntimeError(f"Service initialization failed: {e}") from e


def __parser_delegating_parser(container: Container) -> parser.DelegatingParser:
    return parser.DelegatingParser(parsers=[
        container.get("parser__habr"),
        container.get("parser__reddit"),
        container.get("parser__trashbox"),
    ])


def __telegram_text_factory(_: Container) -> telegram.TextFactory:
    return telegram.TextFactory()


def __telegram_delegating_result_factory(
    container: Container,
) -> telegram.DelegatingResultFactory:
    return telegram.DelegatingResultFactory(
        factories={
            telegram.Text.type(): container.get("telegram_text_factory"),
        }
    )


def __telegram_handler(container: Container) -> telegram.Handler:
    return telegram.Handler(
        parser=container.get("parser_delegating_parser"),
        result_factory=container.get("telegram_delegating_result_factory"),
    )


def __app(container: Container) -> None:
    app = Application.builder().token(container.config.telegram.bot_token).build()
    app.add_handler(InlineQueryHandler(container.get("telegram_handler").inline_query))

    return app.run_polling(allowed_updates=Update.ALL_TYPES)


def __parser_habr(_: Container) -> parser.Parser:
    return habr.Parser(f'{os.name}:{app.name()}:{app.version()}')


def __parser_reddit(container: Container) -> parser.Parser:
    config = container.config.reddit

    return reddit.Parser(
        config.client_id,
        config.client_secret,
        f'{os.name}:{app.name()}:{app.version()} (by /u/{config.app_owner_username})',
    )


def __parser_trashbox(_: Container) -> parser.Parser:
    return trashbox.Parser(f'{os.name}:{app.name()}:{app.version()}')


def load_container(config):
    container = Container(config)

    container.register("parser_delegating_parser", __parser_delegating_parser)
    container.register("telegram_text_factory", __telegram_text_factory)
    container.register("telegram_delegating_result_factory", __telegram_delegating_result_factory)
    container.register("telegram_handler", __telegram_handler)
    container.register("app", __app)

    container.register("parser__habr", __parser_habr)
    container.register("parser__reddit", __parser_reddit)
    container.register("parser__trashbox", __parser_trashbox)

    return container
