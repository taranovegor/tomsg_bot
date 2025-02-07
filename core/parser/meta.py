from html.parser import HTMLParser
from typing import Dict, List, Tuple


class MetaParser(HTMLParser):
    """A parser for extracting meta tags from HTML content."""

    def __init__(self):
        """Initializes the parser and sets up the storage for meta tags."""
        super().__init__()
        self._meta_tags: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        """Handles the start tag of HTML elements and extracts meta tag content."""
        if tag == "meta":
            attr_dict = dict(attrs)
            key = attr_dict.get("name") or attr_dict.get("property")
            if key:
                self._meta_tags[key] = attr_dict.get("content", "")

    def get_meta_tags(self) -> Dict[str, str]:
        """Returns a copy of the extracted meta tags."""
        return self._meta_tags.copy()


class HTMLMetaExtractor:
    """Extracts meta tags from a given HTML content."""

    def __init__(self, html: str):
        """Initializes the extractor with the HTML content."""
        self._parser = MetaParser()
        self._parser.feed(html)

    def extract(self) -> Dict[str, str]:
        """Extracts and returns the meta tags from the HTML content."""
        return self._parser.get_meta_tags()
