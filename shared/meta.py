from html.parser import HTMLParser


class MetaParser(HTMLParser):
    """A parser for extracting meta tags from HTML content."""

    def __init__(self):
        super().__init__()
        self._meta_tags: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]):
        if tag == "meta":
            attr_dict = dict(attrs)
            key = attr_dict.get("name") or attr_dict.get("property")
            if key:
                self._meta_tags[key] = attr_dict.get("content", "")

    def get_meta_tags(self) -> dict[str, str]:
        return self._meta_tags.copy()


class HTMLMetaExtractor:
    """Extracts meta tags from a given HTML content."""

    def __init__(self, html: str):
        self._parser = MetaParser()
        self._parser.feed(html)

    def extract(self) -> dict[str, str]:
        return self._parser.get_meta_tags()
