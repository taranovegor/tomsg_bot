import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


class MediaType(str, enum.Enum):
    """Represents the type of media or content entity."""

    __slots__ = ()

    PHOTO = "photo"
    VIDEO = "video"
    GIF = "gif"
    CONTENT = "content"


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
        return MediaType.PHOTO


@dataclass
class Video(Entity):
    """Represents a video with a resource URL, MIME type, and thumbnail URL."""

    resource_url: str
    mime_type: str
    thumbnail_url: str

    @staticmethod
    def type() -> str:
        """Returns the type of the entity as 'video'."""
        return MediaType.VIDEO


@dataclass
class GIF(Entity):
    """Represents a GIF with a resource URL, MIME type, and thumbnail URL."""

    resource_url: str
    mime_type: str
    thumbnail_url: str

    @staticmethod
    def type() -> str:
        """Returns the type of the entity as 'gif'."""
        return MediaType.GIF


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
        return MediaType.CONTENT


@dataclass(frozen=True)
class FileInfo:
    """Immutable file metadata."""

    path: Path
    size: int
    mime_type: Optional[str] = None
    original_url: Optional[str] = None


@dataclass
class VideoMeta:
    """Stores metadata for a video."""

    width: Optional[int]
    height: Optional[int]
    duration: Optional[int] = None


@dataclass
class PipelineResult:
    content: Content
    resolved_media: list[tuple[Entity, FileInfo]] = field(default_factory=list)
    video_meta: dict[str, VideoMeta] = field(default_factory=dict)
