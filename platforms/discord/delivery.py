import asyncio
import logging
from pathlib import Path

from core.domain.entity import GIF, Entity, FileInfo, PipelineResult, Video
from core.ports.delivery import Delivery
from platforms.discord import DISCORD_MAX_ATTACHMENTS, DISCORD_MAX_FILE_SIZE
from platforms.discord.renderer import DiscordRenderer

TEXT_LIMIT = 2000


class DiscordDelivery(Delivery):
    """Send PipelineResult to a Discord channel or interaction.

    File upload rules (Discord-specific):
    - Max 10 attachments per message.
    - Max 10 MB per file (free tier; override via max_file_size).
    - No media groups — files are sent as plain attachments.
    - GIF/Video/Photo all use the same attachment mechanism.
    - Text is capped at 2000 chars (Discord limit).
    """

    def __init__(
        self,
        renderer: DiscordRenderer,
        max_file_size: int = DISCORD_MAX_FILE_SIZE,
        max_attachments: int = DISCORD_MAX_ATTACHMENTS,
    ):
        self.renderer = renderer
        self.max_file_size = max_file_size
        self.max_attachments = max_attachments

    async def send(self, target, result: PipelineResult) -> None:
        import discord

        text = self.renderer.render_with_link(result.content, max_length=TEXT_LIMIT)

        async def _send(*args, **kwargs):
            try:
                return await target.send(*args, **kwargs, suppress_embeds=True)
            except TypeError:
                return await target.send(*args, **kwargs)

        if not result.resolved_media:
            if text:
                await _send(text)
            return

        files_to_remove: list[Path] = []

        try:
            attachments = []
            for media, fi in result.resolved_media:
                files_to_remove.append(fi.path)
                if fi.size > self.max_file_size:
                    logging.warning(
                        "Skipping %s (%.1f MB exceeds %d MB limit)",
                        fi.original_url or fi.path,
                        fi.size / (1024 * 1024),
                        self.max_file_size // (1024 * 1024),
                    )
                    continue
                filename = self._pick_filename(media, fi)
                attachments.append((fi.path, filename))

            if not attachments:
                if text:
                    await _send(text)
                return

            for i in range(0, len(attachments), self.max_attachments):
                chunk = attachments[i : i + self.max_attachments]
                is_last = i + self.max_attachments >= len(attachments)
                content = text if is_last else None

                files_for_discord = [discord.File(path, filename=name) for path, name in chunk]
                await _send(content=content, files=files_for_discord)

        finally:
            for path in files_to_remove:
                try:
                    await asyncio.to_thread(lambda: path.unlink(missing_ok=True))
                except Exception:
                    logging.exception("Failed to remove %s", path)

    @staticmethod
    def _pick_filename(media: Entity, fi: FileInfo) -> str:
        base = Path(fi.original_url or "file").stem if fi.original_url else "media"
        if isinstance(media, Video):
            ext = ".mp4"
        elif isinstance(media, GIF):
            ext = ".gif"
        else:
            ext = fi.path.suffix or ".jpg"
        return f"{base}{ext}"
