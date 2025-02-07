from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


class Entity(ABC):
    """Abstract base class for entities."""

    @staticmethod
    @abstractmethod
    def type() -> str:
        """Returns the type of the entity."""
        pass


@dataclass
class Link:
    """Represents a link with an optional text."""

    url: str
    text: str | None = None


@dataclass
class Photo(Entity):
    """Represents a photo with resource and thumbnail URLs, and an optional caption."""

    resource_url: str
    thumbnail_url: str | None = None
    caption: str | None = None

    @staticmethod
    def type() -> str:
        """Returns the type of the entity as 'photo'."""
        return "photo"


@dataclass
class Video(Entity):
    """Represents a video with a resource URL, MIME type, and thumbnail URL."""

    resource_url: str
    mime_type: str
    thumbnail_url: str

    @staticmethod
    def type() -> str:
        """Returns the type of the entity as 'video'."""
        return "video"


@dataclass
class GIF(Entity):
    """Represents a GIF with a resource URL, MIME type, and thumbnail URL."""

    resource_url: str
    mime_type: str
    thumbnail_url: str

    @staticmethod
    def type() -> str:
        """Returns the type of the entity as 'gif'."""
        return "gif"


@dataclass
class Content(Entity):
    """Represents content with metadata, text, author, metrics, creation date, and media."""

    backlink: Link
    text: str = None
    author: Link = None
    metrics: list[str] = None
    created_at: datetime = None
    media: list[Photo | Video | GIF] = None

    @staticmethod
    def type() -> str:
        """Returns the type of the entity as 'content'."""
        return "content"
