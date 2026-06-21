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
        try:
            probe = await asyncio.to_thread(ffmpeg.probe, video_path)
        except Exception:
            logging.exception("ffprobe failed for %s", video_path)
            return VideoMeta(width=None, height=None, duration=None)

        width, height, duration = self._parse_probe(probe)
        return VideoMeta(width=width, height=height, duration=duration)

    @staticmethod
    def _parse_probe(
        probe: dict,
    ) -> tuple[int | None, int | None, int | None]:
        width = height = None
        duration = None

        for s in probe.get("streams", []):
            if s.get("codec_type") != "video":
                continue
            if width is None and height is None:
                w = s.get("width")
                h = s.get("height")
                if w is not None and h is not None:
                    width, height = int(w), int(h)
            if duration is None:
                d = s.get("duration")
                if d is not None:
                    try:
                        duration = int(round(float(d)))
                    except Exception:
                        pass

        if duration is None:
            d = probe.get("format", {}).get("duration")
            if d is not None:
                try:
                    duration = int(round(float(d)))
                except Exception:
                    pass

        return width, height, duration
