import html
import re

from core import Content, Link
from core.ports import Renderer
from shared.htmls import sanitize_html


class MessageRenderer(Renderer):
    """
    Render Content into a compact, human-readable string with optional HTML links.
    """

    def render(self, content: Content, max_length: int | None = None) -> str:
        return self._build_parts(content, max_length)

    def render_with_link(self, content: Content, max_length: int | None = None) -> str:
        link_text = self._format_link_as_html(content.backlink)
        link_overhead = len("\n\n" + link_text) if link_text else 0

        base_max = max(max_length - link_overhead, 0) if max_length is not None else None
        base = self._build_parts(content, base_max)

        if link_text:
            if base:
                base += "\n\n" + link_text
            else:
                base = link_text

        return base.strip()

    def _build_parts(self, content: Content, max_length: int | None = None) -> str:
        lines = []

        if content.author:
            lines.append("💁" + self._format_link_as_html(content.author))
        if content.created_at:
            ts = content.created_at.strftime("%d.%m.%y %H:%M %Z")
            if lines:
                lines[-1] = lines[-1] + ", " + ts
            else:
                lines.append(ts)

        if content.text:
            if lines:
                lines.append("")
            lines.append(sanitize_html(content.text))

        if content.metrics:
            if lines:
                lines.append("")
            lines.append("  ".join(content.metrics))

        result = "\n".join(lines).strip()

        if max_length is not None and len(result) > max_length:
            result = self._truncate_html(result, max_length)

        return result

    @staticmethod
    def _truncate_html(text: str, limit: int) -> str:
        _self_closing = frozenset({"br", "img", "hr", "input", "meta", "link"})

        if len(text) <= limit:
            return text

        out: list[str] = []
        buf: list[str] = []
        in_tag = False
        in_entity = False
        stack: list[str] = []
        raw_len = 0

        def _close() -> None:
            nonlocal raw_len
            for tag in reversed(stack):
                closing = f"</{tag}>"
                out.append(closing)
                raw_len += len(closing)
            out.append("...")

        for ch in text:
            if in_tag:
                buf.append(ch)
                if ch == ">":
                    tag_str = "".join(buf)
                    if raw_len + len(tag_str) > limit:
                        _close()
                        return "".join(out)
                    m = re.match(r"</(\w+)", tag_str)
                    if m:
                        if stack and stack[-1] == m.group(1):
                            stack.pop()
                    else:
                        m = re.match(r"<(\w+)", tag_str)
                        if m and m.group(1) not in _self_closing:
                            stack.append(m.group(1))
                    out.append(tag_str)
                    raw_len += len(tag_str)
                    buf = []
                    in_tag = False
                continue

            if ch == "<":
                in_tag = True
                buf = ["<"]
                continue

            if ch == "&":
                in_entity = True
                out.append(ch)
                raw_len += 1
                if raw_len >= limit:
                    _close()
                    return "".join(out)
                continue

            if in_entity:
                out.append(ch)
                raw_len += 1
                if ch == ";":
                    in_entity = False
                if raw_len >= limit:
                    _close()
                    return "".join(out)
                continue

            if raw_len >= limit:
                _close()
                return "".join(out)

            out.append(ch)
            raw_len += 1

        return "".join(out)

    @staticmethod
    def _format_link_as_html(link: Link | None) -> str:
        if not link:
            return ""
        url = link.url or ""
        text = link.text or ""
        if url and text:
            href = html.escape(url, quote=True)
            txt = html.escape(text)
            return f'<a href="{href}">{txt}</a>'
        return html.escape(url or text)
