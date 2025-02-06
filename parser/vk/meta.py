from html.parser import HTMLParser
from typing import Dict, List, Tuple


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._meta_tags: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        if tag == 'meta':
            attr_dict = dict(attrs)
            key = attr_dict.get('name') or attr_dict.get('property')
            if key:
                self._meta_tags[key] = attr_dict.get('content', '')

    def get_meta_tags(self) -> Dict[str, str]:
        return self._meta_tags.copy()


class HTMLMetaExtractor:
    def __init__(self, html: str):
        self._parser = MetaParser()
        self._parser.feed(html)

    def extract(self) -> Dict[str, str]:
        return self._parser.get_meta_tags()
