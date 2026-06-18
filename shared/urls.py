import validators


def is_valid_url(query: str) -> bool:
    """Check whether a query is a valid URL."""
    return bool(validators.url(query))
