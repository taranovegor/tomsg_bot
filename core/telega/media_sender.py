import os
import aiohttp
import tempfile
import asyncio
import ffmpeg
from telegram import InputFile
from telegram.constants import ParseMode
import logging


class MediaSender:
    MAX_SIZE = 20 * 1024 * 1024  # 20MB

    @staticmethod
    async def get_remote_size(url: str) -> int | None:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.head(url, timeout=8) as r:
                    size = r.headers.get("Content-Length")
                    if size and size.isdigit():
                        return int(size)
        except Exception:
            return None

        return None

    @staticmethod
    async def download(url: str) -> str:
        tmpf = tempfile.NamedTemporaryFile(delete=False)
        path = tmpf.name
        tmpf.close()

        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=None) as r:
                    r.raise_for_status()
                    with open(path, "wb") as f:
                        async for chunk in r.content.iter_chunked(65536):
                            f.write(chunk)
            return path
        except Exception:
            try:
                os.remove(path)
            except:
                pass
            raise

    @staticmethod
    async def probe_video(path: str) -> tuple[int | None, int | None]:
        try:
            probe = await asyncio.to_thread(ffmpeg.probe, path)
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video":
                    return stream.get("width"), stream.get("height")
        except Exception:
            return None, None
        return None, None

    @staticmethod
    async def send(msg, media_url: str, mtype: str, caption: str):
        size = await MediaSender.get_remote_size(media_url)

        # If small — send directly from URL
        try:
            if size is not None and size <= MediaSender.MAX_SIZE:
                if mtype == "photo":
                    await msg.reply_photo(media_url, caption=caption, parse_mode=ParseMode.HTML)
                elif mtype == "video":
                    await msg.reply_video(media_url, caption=caption, parse_mode=ParseMode.HTML)
                elif mtype == "gif":
                    await msg.reply_animation(media_url, caption=caption, parse_mode=ParseMode.HTML)
                return
        except Exception:
            pass  # Fall back to file upload

        # Download and send multipart
        path = await MediaSender.download(media_url)
        width, height = (None, None)

        if mtype == "video":
            width, height = await MediaSender.probe_video(path)

        with open(path, "rb") as f:
            inp = InputFile(f)
            if mtype == "video":
                await msg.reply_video(inp, caption=caption, width=width, height=height, parse_mode=ParseMode.HTML)
            elif mtype == "photo":
                await msg.reply_photo(inp, caption=caption, parse_mode=ParseMode.HTML)
            elif mtype == "gif":
                await msg.reply_animation(inp, caption=caption, parse_mode=ParseMode.HTML)

        os.remove(path)
