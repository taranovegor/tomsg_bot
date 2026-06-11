import logging

from bootstrap.container import Container, load_container
from shared.info import name, version
from core.config import load_config


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
