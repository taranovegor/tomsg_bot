from abc import ABC, abstractmethod
from pathlib import Path

from core.domain.entity import FileInfo, VideoMeta


class FileResolver(ABC):
    """Contract: validate, download and store a remote file, return FileInfo."""

    @abstractmethod
    async def resolve(self, url: str) -> FileInfo: ...


class VideoProcessor(ABC):
    """Contract: probe video dimensions and duration from a local file."""

    @abstractmethod
    async def process_video(self, video_path: Path) -> VideoMeta: ...
