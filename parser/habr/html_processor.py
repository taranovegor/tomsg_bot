from html.parser import HTMLParser


class HTMLProcessor(HTMLParser):
    """Processes HTML content and extracts meaningful data."""

    def __init__(self):
        """Initialize the HTML processor."""
        super().__init__()
        self.result = []

    def handle_starttag(self, tag, attrs):
        """Handle opening HTML tags."""
        if tag == "blockquote":
            self.result.append("<blockquote>")
        elif tag == "code":
            self.result.append("<code>")
        elif tag == "pre":
            self.result.append("<pre>")
        elif tag == "img":
            attrs_dict = dict(attrs)
            if "src" in attrs_dict:
                self.result.append(f'<a href="{attrs_dict["src"]}">🖼 Изображение</a>\n')
        elif tag in ["ul", "ol"]:
            self.result.append("\n")
        elif tag == "li":
            self.result.append("- ")

    def handle_endtag(self, tag):
        """Handle closing HTML tags."""
        if tag in ["blockquote", "code", "pre"]:
            self.result.append(f"</{tag}>")
        elif tag in ["ul", "ol"]:
            self.result.append("\n")

    def handle_data(self, data):
        """Handle text data within HTML."""
        self.result.append(data)

    def handle_startendtag(self, tag, attrs):
        """Handle self-closing HTML tags."""
        if tag == "img":
            attrs_dict = dict(attrs)
            if "src" in attrs_dict:
                self.result.append(
                    f'<a href="{attrs_dict["src"]}"><img src="{attrs_dict["src"]}"/></a>'
                )

    def process(self, html: str) -> str:
        """Process input HTML and return formatted text."""
        self.feed(html)
        return "".join(self.result).replace("</p>", "\n")
