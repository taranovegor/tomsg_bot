import os


def name():
    return "tomsg_bot"


def version():
    return os.getenv("VERSION", "undefined")
