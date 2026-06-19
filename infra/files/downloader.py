import asyncio
import os
import re
import urllib.parse
import uuid

import aiofiles
import aiohttp

from .exception import FileDownloadError, FileTooLargeError


class MediaDownloader:
    """Download remote media and provide safe filename utilities."""

    CHUNK_SIZE = 64 * 1024

    def __init__(self, user_agent: str, timeout: int = 120, max_bytes: int = 0):
        self.user_agent = user_agent
        self.timeout = timeout
        # 0 means no limit
        self.max_bytes = max_bytes

    async def download(self, url: str, dest_path: str) -> int:
        """
        - Streams in CHUNK_SIZE increments.
        - Raises FileTooLargeError when max_bytes is set and exceeded (checked
          per-chunk, so a lying or absent Content-Length does not bypass it).
        - Raises FileDownloadError on HTTP error responses.
        - Removes partial file on any exception before re-raising.
        """
        headers = {"User-Agent": self.user_agent}
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            downloaded = 0
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as resp:
                    if resp.status >= 400:
                        raise FileDownloadError(f"HTTP {resp.status} for {url}")

                    async with aiofiles.open(dest_path, "wb") as fd:
                        async for chunk in resp.content.iter_chunked(self.CHUNK_SIZE):
                            if not chunk:
                                break
                            downloaded += len(chunk)
                            if self.max_bytes and downloaded > self.max_bytes:
                                raise FileTooLargeError(
                                    f"Download exceeded {self.max_bytes} bytes: {url}"
                                )
                            await fd.write(chunk)
            return downloaded
        except Exception:
            try:
                if os.path.exists(dest_path):
                    await asyncio.to_thread(os.remove, dest_path)
            except Exception:
                pass
            raise

    @staticmethod
    def safe_filename(url: str, max_len: int = 200) -> str:
        """
        - Uses URL basename when reasonable, sanitizes unsafe chars.
        - Falls back to a generated name with uuid when needed.
        - Ensures the result length does not exceed max_len.
        """
        parsed = urllib.parse.urlparse(url)
        basename = os.path.basename(parsed.path or "")
        if basename:
            name, ext = os.path.splitext(basename)
            safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
            safe_name = re.sub(r"[^\w\-.() ]+", "_", safe_name)
            if safe_name in ("", ".", ".."):
                safe_name = ""
            safe_ext = re.sub(r"[^A-Za-z0-9.]", "", ext) if ext else ""
            candidate = (safe_name + safe_ext) if safe_name else ""
        else:
            candidate = ""

        if not candidate:
            ext = os.path.splitext(parsed.path)[1]
            safe_ext = re.sub(r"[^A-Za-z0-9.]", "", ext) if ext else ""
            candidate = f"{uuid.uuid4().hex}{safe_ext}"

        if len(candidate) > max_len:
            name, ext = os.path.splitext(candidate)
            candidate = name[: max_len - len(ext)] + ext

        return candidate
