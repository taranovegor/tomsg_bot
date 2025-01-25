from html.parser import HTMLParser


class HTMLProcessor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_starttag(self, tag, attrs):
        if tag == 'blockquote':
            self.result.append('<blockquote>')
        elif tag == 'code':
            self.result.append('<code>')
        elif tag == 'pre':
            self.result.append('<pre>')
        elif tag == 'img':
            attrs_dict = dict(attrs)
            if 'src' in attrs_dict:
                self.result.append(f'<a href="{attrs_dict["src"]}">🖼 Изображение</a>\n')
        elif tag in ['ul', 'ol']:
            self.result.append('\n')
        elif tag == 'li':
            self.result.append('- ')

    def handle_endtag(self, tag):
        if tag in ['blockquote', 'code', 'pre']:
            self.result.append(f'</{tag}>')
        elif tag in ['ul', 'ol']:
            self.result.append('\n')

    def handle_data(self, data):
        self.result.append(data)

    def handle_startendtag(self, tag, attrs):
        if tag == 'img':
            attrs_dict = dict(attrs)
            if 'src' in attrs_dict:
                self.result.append(f'<a href="{attrs_dict["src"]}"><img src="{attrs_dict["src"]}"/></a>')

    def process(self, html):
        self.feed(html)
        return ''.join(self.result).replace('</p>', '\n')
