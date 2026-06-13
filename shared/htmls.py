from __future__ import annotations

import html
import re
from urllib.parse import urlparse

TAG_SYNONYMS = {
    "strong": "b",
    "em": "i",
    "ins": "u",
    "del": "s",
    "strike": "s",
    "tg-spoiler": "tg-spoiler",
}

TELEGRAM_WHITELIST_TAGS = frozenset(
    {
        "b",
        "i",
        "u",
        "s",
        "a",
        "code",
        "pre",
        "blockquote",
        "tg-spoiler",
    }
)

ALLOWED_ATTRS: dict[str, frozenset[str]] = {
    "a": frozenset({"href"}),
}

TAG_RE = re.compile(r"</?([\w-]+)((?:\s+\w+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|\S+))?)*)\s*/?>")
ATTR_RE = re.compile(r"""(\w+)\s*=\s*(?:"([^"]*)"|'([^']*)'|(\S+))""")


def _reconstruct_tag(tag_name: str, is_closing: bool, attrs: list[tuple[str, str]]) -> str:
    if is_closing:
        return f"</{tag_name}>"
    attrs_str = "".join(f' {k}="{html.escape(v, quote=True)}"' for k, v in attrs)
    return f"<{tag_name}{attrs_str}>"


def _is_safe_url(url: str) -> bool:
    scheme = urlparse(url).scheme.lower()
    return scheme in ("http", "https", "ftp", "")


def strip_tags(text: str) -> str:
    """Removes HTML tags from a string."""
    return re.sub(r"<.*?>", "", text)


def escape_non_tags(text: str) -> str:
    """We're teaching a soulless machine that <3 is a feeling, not a tag."""
    result = []
    last_index = 0
    for match in re.compile(r"</?[a-zA-Z][^<>]*?>").finditer(text):
        result.append(html.escape(text[last_index : match.start()]))
        result.append(match.group(0))
        last_index = match.end()
    result.append(html.escape(text[last_index:]))
    return "".join(result)


def sanitize_html(text: str) -> str:
    """Sanitize user-provided HTML to only allow Telegram's whitelist tags.

    - Unknown tags are escaped as literal text.
    - Tag synonyms (strong, em, ins, del, strike) are normalized to Telegram equivalents.
    - Attributes are stripped except for ``href`` on ``<a>``.
    - ``href`` values with dangerous schemes (``javascript:``, ``data:``, etc.) are removed.
    """
    result = []
    last_index = 0
    for match in TAG_RE.finditer(text):
        result.append(html.escape(text[last_index : match.start()]))
        raw_tag_name = match.group(1).lower()
        raw_attrs_str = match.group(2).strip()
        is_closing = text[match.start()] == "<" and text[match.start() + 1] == "/"

        tag_name = TAG_SYNONYMS.get(raw_tag_name, raw_tag_name)

        if tag_name not in TELEGRAM_WHITELIST_TAGS:
            result.append(html.escape(match.group(0)))
            last_index = match.end()
            continue

        raw_attrs: list[tuple[str, str]] = []
        for am in ATTR_RE.finditer(raw_attrs_str):
            k = am.group(1).lower()
            v = am.group(2) or am.group(3) or am.group(4) or ""
            allowed = ALLOWED_ATTRS.get(tag_name, frozenset())
            if k not in allowed:
                continue
            if k == "href" and not _is_safe_url(v):
                continue
            raw_attrs.append((k, v))

        result.append(_reconstruct_tag(tag_name, is_closing, raw_attrs))
        last_index = match.end()

    result.append(html.escape(text[last_index:]))
    return "".join(result)
