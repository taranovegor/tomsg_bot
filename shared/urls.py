import validators


def is_valid_url(query: str) -> bool:
    return bool(validators.url(query))
