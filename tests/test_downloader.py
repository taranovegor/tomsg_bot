"""
Tests for MediaDownloader.

- max_bytes is a separate constructor argument from timeout.
- The limit is enforced per-chunk during streaming, not via Content-Length alone.
- The container wires it correctly.
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMediaDownloaderConstructor:
    def test_accepts_separate_timeout_and_max_bytes(self):
        from infra.files.downloader import MediaDownloader

        dl = MediaDownloader("agent", timeout=120, max_bytes=1024)
        assert dl.timeout == 120
        assert dl.max_bytes == 1024

    def test_default_max_bytes_is_zero_meaning_no_limit(self):
        from infra.files.downloader import MediaDownloader

        dl = MediaDownloader("agent")
        assert dl.max_bytes == 0


class TestMediaDownloaderStreamingLimit:
    def _make_session_mock(self, chunks: list[bytes], status: int = 200):
        """Build an aiohttp session mock that streams the given chunks."""

        async def fake_iter_chunked(size):
            for chunk in chunks:
                yield chunk

        mock_resp = MagicMock()
        mock_resp.status = status
        mock_resp.content.iter_chunked = fake_iter_chunked

        mock_get_cm = MagicMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_get_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get_cm)

        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=False)

        return mock_session_cm

    @pytest.mark.asyncio
    async def test_raises_file_too_large_when_stream_exceeds_max_bytes(self, tmp_path):
        """FileTooLarge must fire mid-stream even without a Content-Length header."""
        from infra.files.downloader import MediaDownloader
        from infra.files.exception import FileTooLarge

        dl = MediaDownloader("agent", timeout=30, max_bytes=10)
        dest = str(tmp_path / "out.bin")
        session_mock = self._make_session_mock([b"12345678", b"12345678"])  # 16 bytes > 10

        with patch("infra.files.downloader.aiohttp.ClientSession", return_value=session_mock):
            with pytest.raises(FileTooLarge):
                await dl.download("http://example.com/big.bin", dest)

        assert not os.path.exists(dest), "Partial file must be cleaned up after FileTooLarge"

    @pytest.mark.asyncio
    async def test_succeeds_when_within_max_bytes(self, tmp_path):
        from infra.files.downloader import MediaDownloader

        dl = MediaDownloader("agent", timeout=30, max_bytes=100)
        dest = str(tmp_path / "out.bin")
        session_mock = self._make_session_mock([b"hello"])

        with patch("infra.files.downloader.aiohttp.ClientSession", return_value=session_mock):
            written = await dl.download("http://example.com/small.bin", dest)

        assert written == 5
        assert os.path.exists(dest)

    @pytest.mark.asyncio
    async def test_zero_max_bytes_never_raises(self, tmp_path):
        """max_bytes=0 (default) disables the size check entirely."""
        from infra.files.downloader import MediaDownloader

        dl = MediaDownloader("agent", timeout=30, max_bytes=0)
        dest = str(tmp_path / "out.bin")
        session_mock = self._make_session_mock([b"x" * 1024])

        with patch("infra.files.downloader.aiohttp.ClientSession", return_value=session_mock):
            written = await dl.download("http://example.com/big.bin", dest)

        assert written == 1024


class TestContainerWiresDownloaderCorrectly:
    def test_container_downloader_has_sane_timeout_and_nonzero_max_bytes(self, stub_config):
        """
        The downloader must have a sane timeout and a real max_bytes cap.
        """
        from bootstrap.container import load_container
        from infra.files.downloader import MediaDownloader

        from bootstrap import keys as K
        container = load_container(stub_config)
        dl = container.get(K.FILES_MEDIA_DOWNLOADER)

        assert isinstance(dl, MediaDownloader)
        assert dl.timeout <= 3600, (
            f"timeout={dl.timeout!r} looks like max_bytes was passed as timeout"
        )
        assert dl.max_bytes > 0, "max_bytes is 0 — streaming size cap is not applied"
