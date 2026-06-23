import logging
import os
from typing import Self


class TelegramConfig:
    _required = ("bot_token",)

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.base_url = os.getenv("TELEGRAM_BASE_URL")


class InstagramConfig:
    _required = ("parser_url", "encryption_key")

    def __init__(self):
        self.parser_url = os.getenv("INSTAGRAM_VIDEO_PARSER_URL")
        self.encryption_key = os.getenv("INSTAGRAM_ENCRYPTION_KEY")


class RedditConfig:
    _required = ("client_id", "client_secret")

    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.app_owner_username = os.getenv("REDDIT_APP_OWNER_USERNAME")


class TikTokConfig:
    _required = ("video_resource_url", "thumbnail_resource_url")

    def __init__(self):
        self.video_resource_url = os.getenv("TIKTOK_VIDEO_RESOURCE_URL")
        self.thumbnail_resource_url = os.getenv("TIKTOK_THUMBNAIL_RESOURCE_URL")


class GoogleAnalyticsConfig:
    _required = ()

    def __init__(self):
        self.measurement_id = os.getenv("GA_MEASUREMENT_ID")
        self.secret = os.getenv("GA_SECRET")
        self.user_identifier_salt = os.getenv("GA_UID_SALT")


class VKConfig:
    _required = ("thumbnail_url",)

    def __init__(self):
        self.thumbnail_url = os.getenv("VK_THUMBNAIL_URL")


class YouTubeConfig:
    _required = ("api_key",)

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")


class TumblrConfig:
    _required = ("api_key",)

    def __init__(self):
        self.api_key = os.getenv("TUMBLR_API_KEY")


class Config:
    """Holds the entire configuration for all services."""

    def __init__(self):
        self.version = os.getenv("VERSION")
        self.debug = os.getenv("DEBUG") == "true"
        self.log_level = logging.getLevelName(os.getenv("LOG_LEVEL", "INFO"))
        self.parser_http_timeout = int(os.getenv("PARSER_HTTP_TIMEOUT", "30"))
        self.telegram = TelegramConfig()
        self.instagram = InstagramConfig()
        self.reddit = RedditConfig()
        self.google_analytics = GoogleAnalyticsConfig()
        self.tiktok = TikTokConfig()
        self.tumblr = TumblrConfig()
        self.vk = VKConfig()
        self.youtube = YouTubeConfig()

    def validate(self) -> Self:
        missing = []
        for name in (
            "telegram",
            "instagram",
            "reddit",
            "tiktok",
            "google_analytics",
            "vk",
            "youtube",
            "tumblr",
        ):
            val = getattr(self, name)
            required = getattr(val, "_required", ())
            for field in required:
                if getattr(val, field, None) is None:
                    missing.append(f"{name}.{field}")
        if missing:
            raise RuntimeError("Missing required config variables:\n  " + "\n  ".join(missing))
        return self


def load_config():
    return Config().validate()
