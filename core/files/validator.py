import aiohttp
from .exception import FileTooLarge


class RemoteFileValidator:
    """
    Validate remote file sizes using HTTP HEAD or Range requests.

    Prefers HEAD to read Content-Length, falls back to a 0-0 Range request
    to parse Content-Range when Content-Length is missing.
    """

    def __init__(self, user_agent: str, max_bytes: int, timeout: int = 60):
        """Initialize validator with a User-Agent header and total timeout (seconds)."""
        self.headers = {"User-Agent": user_agent}
        self.max_bytes = max_bytes
        self.timeout = timeout

    async def validate_size(self, url: str) -> None:
        """
        Ensure remote file at `url` does not exceed `max_bytes`.

        Tries to determine size via HEAD then Range. Raises FileTooLarge if
        size is known and exceeds max_bytes. If size cannot be determined,
        the method returns silently.
        """
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            size = await self._get_size_via_head(session, url)

            if size is None:
                size = await self._get_size_via_range(session, url)

            if size is None:
                return

            if size > self.max_bytes:
                raise FileTooLarge(f"Remote file too large: {url}")

    async def _get_size_via_head(
        self, session: aiohttp.ClientSession, url: str
    ) -> int | None:
        """Use HEAD to read Content-Length. Return int size or None if unavailable/invalid."""
        async with session.head(
            url, headers=self.headers, allow_redirects=True
        ) as resp:
            if resp.status >= 400:
                return None

            cl = resp.headers.get("Content-Length")
            try:
                return int(cl) if cl else None
            except ValueError:
                return None

    async def _get_size_via_range(
        self, session: aiohttp.ClientSession, url: str
    ) -> int | None:
        """
        Request the first byte and parse total size from Content-Range header.

        Returns total size as int when parseable, otherwise None.
        """
        headers = dict(self.headers)
        headers["Range"] = "bytes=0-0"

        async with session.get(url, headers=headers, allow_redirects=True) as resp:
            if resp.status not in (200, 206):
                return None

            cr = resp.headers.get("Content-Range")
            if not cr:
                return None

            try:
                return int(cr.split("/")[-1])
            except (ValueError, IndexError):
                return None
