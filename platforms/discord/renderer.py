import html2text

from core.domain.entity import Content, Link
from core.ports.renderer import Renderer


class DiscordRenderer(Renderer):
    """Render Content into Discord Markdown with an optional source link."""

    def __init__(self) -> None:
        self._converter = html2text.HTML2Text()
        self._converter.body_width = 0
        self._converter.ignore_links = False
        self._converter.ignore_images = True
        self._converter.protect_links = False
        self._converter.mark_code = False
        self._converter.unicode_snob = True
        self._converter.use_automatic_links = False
        self._converter.emphasis_mark = "*"
        self._converter.strong_mark = "**"

    def render(self, content: Content, max_length: int | None = None) -> str:
        return self._build_parts(content, max_length)

    def render_with_link(self, content: Content, max_length: int | None = None) -> str:
        link_text = self._format_link(content.backlink)
        link_overhead = len("\n\n" + link_text) if link_text else 0
        base_max = max(max_length - link_overhead, 0) if max_length is not None else None
        base = self._build_parts(content, base_max)
        if link_text:
            base = (base + "\n\n" + link_text) if base else link_text
        return base.strip()

    def _build_parts(self, content: Content, max_length: int | None = None) -> str:
        lines = []
        if content.author:
            lines.append(self._format_author(content.author))
        if content.created_at:
            ts = content.created_at.strftime("%d.%m.%y %H:%M %Z")
            if lines:
                lines[-1] = lines[-1] + ", " + ts
            else:
                lines.append(ts)
        if content.text:
            if lines:
                lines.append("")
            lines.append(self._converter.handle(content.text).strip())
        if content.metrics:
            if lines:
                lines.append("")
            lines.append("  ".join(content.metrics))
        result = "\n".join(lines).strip()
        if max_length is not None and len(result) > max_length:
            budget = max(0, max_length - 3)
            truncated = result[:budget].rstrip()
            if truncated.rfind("[") > truncated.rfind("]"):
                idx = truncated.rfind("[")
                truncated = truncated[:idx]
            result = truncated + "..."
        return result

    @staticmethod
    def _format_link(link: Link | None) -> str:
        if not link:
            return ""
        url = link.url or ""
        text = link.text or ""
        if url and text:
            return f"[{text}]({url})"
        return url or text

    @staticmethod
    def _format_author(link: Link) -> str:
        url = link.url or ""
        text = link.text or ""
        label = f"[{text}]({url})" if url and text else (url or text)
        return f"\U0001f481 {label}"
