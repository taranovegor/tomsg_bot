import logging
import os

from core.config import load_config
from core.container import Container, load_container


class Instance:
    """A class that represents an instance tied to a container."""

    def __init__(self, container: Container):
        self.container = container

    def run(self):
        """Runs the application instance."""
        self.container.get("app")


def init():
    """Loads configuration, initializes, and returns an Instance."""
    config = load_config()

    logging.basicConfig(
        format="[%(levelname)s] %(asctime)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=config.log_level,
    )

    logging.debug("Initializing application...")
    container = load_container(config)
    logging.debug("Container loaded successfully.")

    return Instance(container)


def name():
    """Returns the name of the bot."""
    return "tomsg_bot"


def version():
    """Returns the version of the bot."""
    return os.getenv("VERSION", "undefined")
