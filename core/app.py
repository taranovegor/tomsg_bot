import os

from core.config import load_config
from core.container import Container, load_container


class Instance:
    def __init__(self, container: Container):
        self.container = container

    def run(self):
        self.container.get("app")


def init():
    return Instance(load_container(load_config()))


def name():
    return "tomsg_bot"


def version():
    return os.getenv("VERSION", "undefined")
