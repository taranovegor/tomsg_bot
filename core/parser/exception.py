class InvalidUrlError(Exception):
    """Exception raised when an unsupported or invalid URL is provided."""

    def __init__(self, *args, **kwargs):
        if not args:
            args = ("The provided URL is not supported.",)

        super().__init__(*args, **kwargs)


class ParserNotFoundError(Exception):
    """Exception raised when no suitable parser is found for the given input."""

    pass


class ParseError(Exception):
    """Exception raised when an error occurs during parsing."""

    pass
