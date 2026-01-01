import html
import re


def strip_tags(text: str) -> str:
    """Removes HTML tags from a string."""
    return re.sub(r"<.*?>", "", text)


def escape_non_tags(text: str) -> str:
    """We’re teaching a soulless machine that <3 is a feeling, not a tag."""
    result = []
    last_index = 0
    for match in re.compile(r"</?[a-zA-Z][^<>]*?>").finditer(text):
        result.append(html.escape(text[last_index : match.start()]))
        result.append(match.group(0))
        last_index = match.end()
    result.append(html.escape(text[last_index:]))
    return "".join(result)
