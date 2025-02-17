import logging
import os


class TelegramConfig:
    """Holds the configuration for the Telegram bot."""

    def __init__(self):
        """Initializes with the bot token from the environment variable."""
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")


class InstagramConfig:
    """Holds the configuration for Instagram-related settings."""

    def __init__(self):
        """Initializes with Instagram video and thumbnail URLs from environment variables."""
        self.video_meta_url = os.getenv("INSTAGRAM_VIDEO_META_URL")
        self.video_storage_url = os.getenv("INSTAGRAM_VIDEO_STORAGE_URL")
        self.thumbnail_url = os.getenv("INSTAGRAM_THUMBNAIL_URL")


class RedditConfig:
    """Holds the configuration for Reddit-related settings."""

    def __init__(self):
        """Initializes with Reddit credentials and app owner username from environment variables."""
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.app_owner_username = os.getenv("REDDIT_APP_OWNER_USERNAME")


class TikTokConfig:
    """Holds the configuration for TikTok-related settings."""

    def __init__(self):
        """Initializes with TikTok video and thumbnail resource URLs from environment variables."""
        self.video_resource_url = os.getenv("TIKTOK_VIDEO_RESOURCE_URL")
        self.thumbnail_resource_url = os.getenv("TIKTOK_THUMBNAIL_RESOURCE_URL")


class GoogleAnalyticsConfig:
    """Holds the configuration for Google Analytics."""

    def __init__(self):
        """Initializes with the GA measurement ID and secret from environment variables."""
        self.measurement_id = os.getenv("GA_MEASUREMENT_ID")
        self.secret = os.getenv("GA_SECRET")
        self.user_identifier_salt = os.getenv("GA_UID_SALT")


class VKConfig:
    """Holds the configuration for VK-related settings."""

    def __init__(self):
        """Initializes with VK thumbnail URL from the environment variable."""
        self.thumbnail_url = os.getenv("VK_THUMBNAIL_URL")


class Config:
    """Holds the entire configuration for all services."""

    def __init__(self):
        """Initializes the configuration with environment variables and specific service configurations."""
        self.version = os.getenv("VERSION")
        self.debug = os.getenv("DEBUG") == "true"
        self.log_level = logging.getLevelName(os.getenv("LOG_LEVEL"))
        self.telegram = TelegramConfig()
        self.instagram = InstagramConfig()
        self.reddit = RedditConfig()
        self.google_analytics = GoogleAnalyticsConfig()
        self.tiktok = TikTokConfig()
        self.vk = VKConfig()


def load_config():
    """Loads and returns the complete configuration."""
    return Config()
