import os


class TelegramConfig:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")


class Config:
    def __init__(self):
        self.version = os.getenv("VERSION")
        self.debug = os.getenv("DEBUG") == "true"
        self.telegram = TelegramConfig()


def load_config():
    return Config()
