import re
from urllib.parse import urlparse
import validators


class UrlUtils:
    SIMPLE_URL_REGEX = re.compile(r"https?://\S+")

    @staticmethod
    def is_valid_url(text: str) -> bool:
        return bool(validators.url(text))

    @staticmethod
    def extract_url(text: str) -> str | None:
        if validators.url(text):
            return text

        match = UrlUtils.SIMPLE_URL_REGEX.search(text)
        if match:
            return match.group(0).rstrip('.,)\"\'')
        return None

    @staticmethod
    def hostname(url: str) -> str:
        return urlparse(url).netloc
