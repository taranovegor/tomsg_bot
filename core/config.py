import os


class TelegramConfig:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")


class RedditConfig:
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.app_owner_username = os.getenv("REDDIT_APP_OWNER_USERNAME")


class Config:
    def __init__(self):
        self.version = os.getenv("VERSION")
        self.debug = os.getenv("DEBUG") == "true"
        self.telegram = TelegramConfig()
        self.reddit = RedditConfig()


def load_config():
    return Config()
