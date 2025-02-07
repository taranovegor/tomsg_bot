class ParserNotFoundError(Exception):
    """Exception raised when no suitable parser is found for the given input."""

    pass


class ParseError(Exception):
    """Exception raised when an error occurs during parsing."""

    pass
