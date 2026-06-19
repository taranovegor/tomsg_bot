from abc import ABC, abstractmethod

from core.domain.entity import Content
from core.exceptions import ParserNotFoundError


class Parser(ABC):
    """Abstract base class for parsers, defining the structure for parsing content."""

    @abstractmethod
    def supports(self, string: str) -> bool:
        pass

    @abstractmethod
    def parse(self, string: str) -> Content:
        pass


class DelegatingParser(Parser):
    """A parser that delegates parsing to a list of other parsers."""

    def __init__(self, parsers: list[Parser]):
        self.parsers = parsers

    def supports(self, string: str) -> bool:
        return any(parser.supports(string) for parser in self.parsers)

    def parse(self, string: str) -> Content:
        for parser in self.parsers:
            if parser.supports(string):
                return parser.parse(string)
        raise ParserNotFoundError(f"Parser not found for string: {string}")
