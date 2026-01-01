from pathlib import Path

from .entity import FileInfo
from .validator import RemoteFileValidator
from .downloader import MediaDownloader
from .storage import LocalStorage


class FileResolver:
    """Validate remote files, download them into local storage and return FileInfo."""

    def __init__(
        self,
        validator: RemoteFileValidator,
        downloader: MediaDownloader,
        storage: LocalStorage,
    ):
        self.validator = validator
        self.downloader = downloader
        self.storage = storage

    async def resolve(self, url: str) -> FileInfo:
        """
        Validate URL and size, download to storage and return FileInfo.

        Args:
            url: Remote file URL.

        Returns:
            FileInfo with local path, size (bytes), and original URL.

        Raises:
            Propagates validation or download exceptions.
        """
        await self.validator.validate_size(url)

        filename = self.downloader.safe_filename(url)
        path: Path = self.storage.get_path(filename)

        size = await self.downloader.download(url, str(path))

        return FileInfo(
            path=path,
            size=size,
            original_url=url,
        )
