import asyncio
import logging
from pathlib import Path

import ffmpeg

from core.ports import VideoProcessor as VideoProcessorPort
from infra.files.storage import LocalStorage
from infra.media.entity import VideoMeta


class VideoProcessor(VideoProcessorPort):
    """Utilities to probe video info (dimensions, duration)."""

    def __init__(self, storage: LocalStorage):
        self.storage = storage

    async def process_video(self, video_path: Path) -> VideoMeta:
        dim_task = asyncio.create_task(self.probe_dimensions(video_path))
        dur_task = asyncio.create_task(self.probe_duration(video_path))

        width, height = await dim_task
        duration = await dur_task

        return VideoMeta(
            width=width,
            height=height,
            duration=duration,
        )

    @staticmethod
    async def probe_duration(filepath: Path) -> int | None:
        """
        Prefers per-video-stream duration; falls back to format-level duration.
        Rounds to nearest second.
        """
        try:
            probe = await asyncio.to_thread(ffmpeg.probe, filepath)
            streams = probe.get("streams", [])
            for s in streams:
                if s.get("codec_type") == "video":
                    d = s.get("duration")
                    if d is not None:
                        try:
                            return int(round(float(d)))
                        except Exception:
                            pass
            d = probe.get("format", {}).get("duration")
            if d is not None:
                try:
                    return int(round(float(d)))
                except Exception:
                    pass
            return None
        except Exception:
            logging.exception("ffprobe failed for %s", filepath)
            return None

    @staticmethod
    async def probe_dimensions(filepath: Path) -> tuple[int | None, int | None]:
        try:
            probe = await asyncio.to_thread(ffmpeg.probe, filepath)
            streams = probe.get("streams", [])
            for s in streams:
                if s.get("codec_type") == "video":
                    width = s.get("width")
                    height = s.get("height")
                    if width is not None and height is not None:
                        return int(width), int(height)
            return None, None
        except Exception:
            logging.exception("ffprobe failed for %s", filepath)
            return None, None
