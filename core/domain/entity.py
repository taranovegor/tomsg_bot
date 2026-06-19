import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


class MediaType(enum.StrEnum):
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
    def type() -> MediaType:
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
    def type() -> MediaType:
        return MediaType.PHOTO


@dataclass
class Video(Entity):
    """Represents a video with a resource URL, MIME type, and thumbnail URL."""

    resource_url: str
    mime_type: str
    thumbnail_url: str

    @staticmethod
    def type() -> MediaType:
        return MediaType.VIDEO


@dataclass
class GIF(Entity):
    """Represents a GIF with a resource URL, MIME type, and thumbnail URL."""

    resource_url: str
    mime_type: str
    thumbnail_url: str

    @staticmethod
    def type() -> MediaType:
        return MediaType.GIF


@dataclass
class Content(Entity):
    """Represents content with metadata, text, author, metrics, creation date, and media."""

    backlink: Link
    text: str | None = None
    author: Link | None = None
    metrics: list[str] | None = None
    created_at: datetime | None = None
    media: list[Photo | Video | GIF] | None = None

    @staticmethod
    def type() -> MediaType:
        return MediaType.CONTENT


@dataclass(frozen=True)
class FileInfo:
    """Immutable file metadata."""

    path: Path
    size: int
    mime_type: str | None = None
    original_url: str | None = None


@dataclass
class VideoMeta:
    """Stores metadata for a video."""

    width: int | None
    height: int | None
    duration: int | None = None


@dataclass
class PipelineResult:
    content: Content
    resolved_media: list[tuple[Entity, FileInfo]] = field(default_factory=list)
    video_meta: dict[str, VideoMeta] = field(default_factory=dict)
