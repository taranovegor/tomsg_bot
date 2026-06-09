import asyncio
import logging
from dataclasses import dataclass, field

from core.files.entity import FileInfo
from core.files.resolver import FileResolver
from core.media.entity import VideoMeta
from core.media.processor import VideoProcessor
from core.parser import Parser, ParserNotFoundError
from core.parser.entity import Content, Entity, Video
from core.parser.exception import InvalidUrlError
from core.utils.urls import is_valid_url


@dataclass
class PipelineResult:
    content: Content
    resolved_media: list[tuple[Entity, FileInfo]] = field(default_factory=list)
    video_meta: dict[str, VideoMeta] = field(default_factory=dict)


class Pipeline:
    """validate -> route -> parse -> resolve files -> process video"""

    def __init__(
        self,
        parser: Parser,
        file_resolver: FileResolver,
        video_processor: VideoProcessor,
    ):
        self.parser = parser
        self.file_resolver = file_resolver
        self.video_processor = video_processor

    async def run(self, url: str) -> PipelineResult:
        if not is_valid_url(url):
            raise InvalidUrlError()

        content = await asyncio.to_thread(self.parser.parse, url)

        if not content.media:
            return PipelineResult(content=content)

        resolve_tasks = [
            self.file_resolver.resolve(m.resource_url) for m in content.media
        ]
        raw_results = await asyncio.gather(*resolve_tasks, return_exceptions=True)

        successful_pairs = []
        for media, res in zip(content.media, raw_results):
            if isinstance(res, Exception):
                logging.warning(
                    "Failed to resolve %s: %s", media.resource_url, res
                )
                continue
            successful_pairs.append((media, res))

        if not successful_pairs:
            return PipelineResult(content=content)

        video_meta = {}
        for media, fi in successful_pairs:
            if isinstance(media, Video):
                try:
                    meta = await self.video_processor.process_video(fi.path)
                    video_meta[media.resource_url] = meta
                except Exception as e:
                    logging.warning(
                        "Failed to process video %s: %s",
                        media.resource_url,
                        e,
                    )

        return PipelineResult(
            content=content,
            resolved_media=successful_pairs,
            video_meta=video_meta,
        )
