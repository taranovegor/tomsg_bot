import html
from typing import Optional

from core import Content, Link
from core.ports import Renderer
from shared.htmls import sanitize_html


class MessageRenderer(Renderer):
    """
    Render Content into a compact, human-readable string with optional HTML links.
    """

    def render(self, content: Content) -> str:
        """
        Produce a compact textual summary of `content`.

        Includes author (as an HTML link if available), creation timestamp,
        sanitized text (only Telegram-whitelist HTML tags preserved), and
        metrics. Returns the resulting text with surrounding whitespace trimmed.
        """
        parts = []

        if content.author:
            parts.append("💁" + self._format_link_as_html(content.author))
        if content.created_at:
            ts = content.created_at.strftime("%d.%m.%y %H:%M %Z")
            if parts:
                parts[-1] = parts[-1] + ", " + ts
            else:
                parts.append(ts)
        if content.author or content.created_at:
            parts.append("")

        if content.text:
            parts.append(sanitize_html(content.text))
            parts.append("")
        elif content.author or content.created_at:
            parts.append("")

        if content.metrics:
            parts.append("  ".join(content.metrics))

        return "\n".join(parts).strip()

    def render_with_link(self, content: Content) -> str:
        """
        Render the content and append an optional backlink.

        Uses `render` as a base, then adds a backlink anchor (if present) on a
        separate line. Ensures spacing is tidy and returns the trimmed result.
        """
        base = self.render(content)
        link_text = self._format_link_as_html(content.backlink)
        if base:
            base += "\n\n"

        if link_text:
            base += link_text

        return base.strip()

    @staticmethod
    def _format_link_as_html(link: Optional[Link]) -> str:
        """
        Return an HTML anchor for a Link when both url and text are present.

        If `link` is None, returns an empty string. If only a url is present,
        returns the url string unchanged.
        """
        if not link:
            return ""
        url = link.url or ""
        text = link.text or ""
        if url and text:
            href = html.escape(url, quote=True)
            txt = html.escape(text)
            return f'<a href="{href}">{txt}</a>'
        return html.escape(url or text)
