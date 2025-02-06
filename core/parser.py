from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


class NoParserFound(Exception):
    pass


class UnableToParse(Exception):
    pass


class Entity(ABC):
    @staticmethod
    @abstractmethod
    def type() -> str:
        pass


@dataclass
class Link:
    url: str
    text: str


@dataclass
class Text(Entity):
    author: Link
    created_at: datetime|None
    metrics: List[str]
    content: str
    backlink: Link

    @staticmethod
    def type() -> str:
        return "text"


@dataclass()
class Video(Entity):
    resource_url: str
    mime_type: str
    thumbnail_url: str
    backlink: Link
    caption: str = None
    author: Link|None = None
    created_at: datetime|None = None

    @staticmethod
    def type() -> str:
        return "video"


class Parser(ABC):
    @abstractmethod
    def supports(self, string: str) -> bool:
        pass

    @abstractmethod
    def parse(self, string: str) -> Entity:
        pass


class DelegatingParser(Parser):
    def __init__(self, parsers: List[Parser]):
        self.parsers = parsers

    def supports(self, string: str) -> bool:
        return any(parser.supports(string) for parser in self.parsers)

    def parse(self, string: str) -> Entity:
        for parser in self.parsers:
            if parser.supports(string):
                return parser.parse(string)
        raise NoParserFound
