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
    """Initializes and returns an Instance with a loaded container and configuration."""
    return Instance(load_container(load_config()))


def name():
    """Returns the name of the bot."""
    return "tomsg_bot"


def version():
    """Returns the version of the bot."""
    return os.getenv("VERSION", "undefined")
