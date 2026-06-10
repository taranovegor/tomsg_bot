"""
Tests for core/pipeline — the platform-neutral processing pipeline.

Uses fakes for parser, file resolver, and video processor so no real
network or filesystem I/O is exercised.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.domain.entity import Content, Photo, Video, GIF, Link, FileInfo, VideoMeta, PipelineResult
from core.exceptions import InvalidUrlError
from core.pipeline import Pipeline


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeParser:
    def __init__(self, content: Content):
        self._content = content
        self.supports = MagicMock(return_value=True)

    def parse(self, url: str) -> Content:
        return self._content


class FakeFailingParser:
    def supports(self, url: str) -> bool:
        return True

    def parse(self, url: str) -> Content:
        msg = f"Parser not found for string: {url}"
        from core.exceptions import ParserNotFoundError
        raise ParserNotFoundError(msg)


class FakeFileResolver:
    def __init__(self):
        self.resolve = AsyncMock()


class FakeVideoProcessor:
    def __init__(self):
        self.process_video = AsyncMock()


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------


class TestPipelineUrlValidation:
    @pytest.mark.asyncio
    async def test_rejects_invalid_url(self):
        pipeline = Pipeline(
            parser=MagicMock(),
            file_resolver=FakeFileResolver(),
            video_processor=FakeVideoProcessor(),
        )
        with pytest.raises(InvalidUrlError):
            await pipeline.run("not a url")

    @pytest.mark.asyncio
    async def test_rejects_empty_string(self):
        pipeline = Pipeline(
            parser=MagicMock(),
            file_resolver=FakeFileResolver(),
            video_processor=FakeVideoProcessor(),
        )
        with pytest.raises(InvalidUrlError):
            await pipeline.run("")

    @pytest.mark.asyncio
    async def test_accepts_valid_url(self):
        content = Content(backlink=Link(url="https://example.com"))
        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=FakeFileResolver(),
            video_processor=FakeVideoProcessor(),
        )
        result = await pipeline.run("https://example.com/post/1")
        assert isinstance(result, PipelineResult)
        assert result.content is content


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


class TestPipelineParsing:
    @pytest.mark.asyncio
    async def test_parser_not_found_propagates(self):
        pipeline = Pipeline(
            parser=FakeFailingParser(),
            file_resolver=FakeFileResolver(),
            video_processor=FakeVideoProcessor(),
        )
        from core.exceptions import ParserNotFoundError
        with pytest.raises(ParserNotFoundError):
            await pipeline.run("https://unsupported.example.com")

    @pytest.mark.asyncio
    async def test_text_only_content_no_media_resolution(self):
        """Content without media skips file resolution entirely."""
        content = Content(
            backlink=Link(url="https://example.com"),
            text="Hello world",
        )
        resolver = FakeFileResolver()
        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=FakeVideoProcessor(),
        )
        result = await pipeline.run("https://example.com/post/1")

        assert result.content is content
        assert result.resolved_media == []
        resolver.resolve.assert_not_called()


# ---------------------------------------------------------------------------
# File resolution
# ---------------------------------------------------------------------------


class TestPipelineFileResolution:
    @pytest.mark.asyncio
    async def test_resolves_all_media(self):
        content = Content(
            backlink=Link(url="https://example.com"),
            media=[
                Photo(resource_url="https://cdn.test/photo1.jpg"),
                Photo(resource_url="https://cdn.test/photo2.jpg"),
            ],
        )
        fake_fi_1 = FileInfo(path="/tmp/photo1.jpg", size=100)
        fake_fi_2 = FileInfo(path="/tmp/photo2.jpg", size=200)

        resolver = FakeFileResolver()
        resolver.resolve = AsyncMock(side_effect=[fake_fi_1, fake_fi_2])

        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=FakeVideoProcessor(),
        )
        result = await pipeline.run("https://example.com/gallery")

        assert len(result.resolved_media) == 2
        assert result.resolved_media[0] == (content.media[0], fake_fi_1)
        assert result.resolved_media[1] == (content.media[1], fake_fi_2)

    @pytest.mark.asyncio
    async def test_skips_failed_resolutions_gracefully(self):
        content = Content(
            backlink=Link(url="https://example.com"),
            media=[
                Photo(resource_url="https://cdn.test/ok.jpg"),
                Photo(resource_url="https://cdn.test/broken.jpg"),
            ],
        )
        fake_fi = FileInfo(path="/tmp/ok.jpg", size=100)

        resolver = FakeFileResolver()
        resolver.resolve = AsyncMock(
            side_effect=[fake_fi, RuntimeError("connection reset")]
        )

        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=FakeVideoProcessor(),
        )
        result = await pipeline.run("https://example.com/gallery")

        assert len(result.resolved_media) == 1
        assert result.resolved_media[0][0] is content.media[0]
        assert result.resolved_media[0][1] is fake_fi

    @pytest.mark.asyncio
    async def test_empty_resolved_media_when_all_fail(self):
        content = Content(
            backlink=Link(url="https://example.com"),
            media=[
                Photo(resource_url="https://cdn.test/broken1.jpg"),
                Photo(resource_url="https://cdn.test/broken2.jpg"),
            ],
        )
        resolver = FakeFileResolver()
        resolver.resolve = AsyncMock(
            side_effect=[RuntimeError("err1"), RuntimeError("err2")]
        )

        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=FakeVideoProcessor(),
        )
        result = await pipeline.run("https://example.com/gallery")

        assert result.resolved_media == []


# ---------------------------------------------------------------------------
# Video processing
# ---------------------------------------------------------------------------


class TestPipelineVideoProcessing:
    @pytest.mark.asyncio
    async def test_processes_video_and_stores_meta(self):
        content = Content(
            backlink=Link(url="https://example.com"),
            media=[
                Video(
                    resource_url="https://cdn.test/video.mp4",
                    mime_type="video/mp4",
                    thumbnail_url="https://cdn.test/thumb.jpg",
                ),
            ],
        )
        fake_fi = FileInfo(path="/tmp/video.mp4", size=5000)
        fake_meta = VideoMeta(width=1920, height=1080, duration=30)

        resolver = FakeFileResolver()
        resolver.resolve = AsyncMock(return_value=fake_fi)

        processor = FakeVideoProcessor()
        processor.process_video = AsyncMock(return_value=fake_meta)

        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=processor,
        )
        result = await pipeline.run("https://example.com/video")

        assert result.video_meta["https://cdn.test/video.mp4"] is fake_meta
        processor.process_video.assert_called_once_with(fake_fi.path)

    @pytest.mark.asyncio
    async def test_skips_video_processing_on_non_video_media(self):
        content = Content(
            backlink=Link(url="https://example.com"),
            media=[Photo(resource_url="https://cdn.test/photo.jpg")],
        )
        fake_fi = FileInfo(path="/tmp/photo.jpg", size=100)

        resolver = FakeFileResolver()
        resolver.resolve = AsyncMock(return_value=fake_fi)

        processor = FakeVideoProcessor()

        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=processor,
        )
        result = await pipeline.run("https://example.com/photo")

        assert result.video_meta == {}
        processor.process_video.assert_not_called()

    @pytest.mark.asyncio
    async def test_video_processing_failure_does_not_crash_pipeline(self):
        content = Content(
            backlink=Link(url="https://example.com"),
            media=[
                Video(
                    resource_url="https://cdn.test/video.mp4",
                    mime_type="video/mp4",
                    thumbnail_url="https://cdn.test/thumb.jpg",
                ),
            ],
        )
        fake_fi = FileInfo(path="/tmp/video.mp4", size=5000)

        resolver = FakeFileResolver()
        resolver.resolve = AsyncMock(return_value=fake_fi)

        processor = FakeVideoProcessor()
        processor.process_video = AsyncMock(
            side_effect=RuntimeError("ffprobe failed")
        )

        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=processor,
        )
        result = await pipeline.run("https://example.com/video")

        assert result.video_meta == {}
        assert len(result.resolved_media) == 1


# ---------------------------------------------------------------------------
# Mixed content
# ---------------------------------------------------------------------------


class TestPipelineMixedContent:
    @pytest.mark.asyncio
    async def test_handles_photos_videos_and_gifs(self, tmp_path):
        content = Content(
            backlink=Link(url="https://example.com"),
            media=[
                Photo(resource_url="https://cdn.test/p.jpg"),
                Video(
                    resource_url="https://cdn.test/v.mp4",
                    mime_type="video/mp4",
                    thumbnail_url="https://cdn.test/v_thumb.jpg",
                ),
                GIF(
                    resource_url="https://cdn.test/g.gif",
                    mime_type="image/gif",
                    thumbnail_url="https://cdn.test/g_thumb.jpg",
                ),
            ],
        )
        fi_photo = FileInfo(path=tmp_path / "p.jpg", size=100)
        fi_video = FileInfo(path=tmp_path / "v.mp4", size=5000)
        fi_gif = FileInfo(path=tmp_path / "g.gif", size=200)
        fake_meta = VideoMeta(width=640, height=480, duration=15)

        resolver = FakeFileResolver()
        resolver.resolve = AsyncMock(side_effect=[fi_photo, fi_video, fi_gif])

        processor = FakeVideoProcessor()
        processor.process_video = AsyncMock(return_value=fake_meta)

        pipeline = Pipeline(
            parser=FakeParser(content),
            file_resolver=resolver,
            video_processor=processor,
        )
        result = await pipeline.run("https://example.com/mixed")

        assert len(result.resolved_media) == 3
        assert "https://cdn.test/v.mp4" in result.video_meta
        processor.process_video.assert_called_once_with(fi_video.path)
