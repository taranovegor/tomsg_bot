from abc import ABC, abstractmethod
from core import Content, ParserNotFoundError


class Parser(ABC):
    """Abstract base class for parsers, defining the structure for parsing content."""

    @abstractmethod
    def supports(self, string: str) -> bool:
        """Checks if the parser supports the given string."""
        pass

    @abstractmethod
    def parse(self, string: str) -> Content:
        """Parses the string and returns the corresponding content."""
        pass


class DelegatingParser(Parser):
    """A parser that delegates parsing to a list of other parsers."""

    def __init__(self, parsers: list[Parser]):
        """Initializes the delegating parser with a list of parsers."""
        self.parsers = parsers

    def supports(self, string: str) -> bool:
        """Checks if any of the parsers support the given string."""
        return any(parser.supports(string) for parser in self.parsers)

    def parse(self, string: str) -> Content:
        """Delegates parsing to the appropriate parser based on support."""
        for parser in self.parsers:
            if parser.supports(string):
                return parser.parse(string)
        raise ParserNotFoundError(f"Parser not found for string: {string}")
