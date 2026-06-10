import re
import validators

URL_REGEX = re.compile(r"https?://[\w./-]+")


def is_valid_url(query: str) -> bool:
    """Check whether a query is a valid URL."""
    return bool(validators.url(query) or URL_REGEX.match(query))
