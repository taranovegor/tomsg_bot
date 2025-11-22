class MessageFormatter:
    @staticmethod
    def text(content) -> str:
        parts = []

        if content.author:
            parts.append(f"💁<a href='{content.author.url}'>{content.author.text or content.author.url}</a>")

        if content.created_at:
            parts.append(content.created_at.strftime("%d.%m.%y %H:%M %Z"))

        header = ", ".join(parts)
        body = content.text or ""
        metrics = " ".join(content.metrics) if content.metrics else ""

        text = ""
        if header:
            text += header + "\n"
        if body:
            text += body + "\n\n"
        if metrics:
            text += metrics

        return text.strip()

    @staticmethod
    def with_backlink(body: str, emoji: str, link) -> str:
        return f"{body}\n\n{emoji}<a href='{link.url}'>{link.text or link.url}</a>"
