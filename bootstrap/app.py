import logging

from bootstrap.container import Container, load_container
from core.config import load_config
from shared.info import name, version  # noqa: F401


class Instance:
    """A class that represents an instance tied to a container."""

    def __init__(self, container: Container):
        self.container = container

    def run(self):
        self.container.get("app")


def init():
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
