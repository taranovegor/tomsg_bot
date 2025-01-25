from html.parser import HTMLParser
from html import escape


def is_multiline_code(node):
    for child in node.get('children', []):
        if child['type'] == 'text' and '\n' in child['data']:
            return True
    return False


def is_punctuation(data):
    punctuation = [".", ",", "!", "?", ":", ";", "*"]
    return any(data.startswith(symbol) for symbol in punctuation)


def get_next_sibling(node):
    parent = node.get('parent')
    if not parent:
        return None

    siblings = parent.get('children', [])
    for i, child in enumerate(siblings):
        if child is node and i + 1 < len(siblings):
            return siblings[i + 1]
    return None


def has_non_block_sibling(node):
    sibling = get_next_sibling(node)
    if not sibling:
        return False

    if sibling['data'] == 'blockquote':
        return False

    if sibling.get('children') and sibling['children'][0]['data'] == 'code':
        return False

    return True


def process_node(node):
    output = []

    if node['type'] == 'text':
        text = node['data'].strip()
        if text:
            output.append(escape(text))
        return ''.join(output)

    if node['type'] == 'element':
        tag = node['data']

        if tag == 'code':
            if is_multiline_code(node):
                output.append('<pre>')
            elif node.get('parent', {}).get('data') == 'p' and node.get('parent', {}).get('children', [{}])[0].get('data') == 'code':
                output.append('<code>')
            else:
                output.append(' <code>')

            for child in node.get('children', []):
                output.append(process_node(child))

            if is_multiline_code(node):
                output.append('</pre>')
            else:
                output.append('</code>')
                if get_next_sibling(node) and not is_punctuation(get_next_sibling(node).get('data', '')):
                    output.append(' ')

        elif tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for child in node.get('children', []):
                output.append(process_node(child))
            output.append('\n\n')

        elif tag in ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del']:
            output.append(f'<{tag}>')
            for child in node.get('children', []):
                output.append(process_node(child))
            output.append(f'</{tag}>')

        elif tag == 'blockquote':
            output.append('<blockquote>')
            for child in node.get('children', []):
                output.append(process_node(child))
            output.append('</blockquote>\n')

        elif tag == 'a':
            href = ''
            for attr in node.get('attrs', []):
                if attr['key'] == 'href':
                    href = escape(attr['value'])
                    break
            if href:
                output.append(f' <a href="{href}">')
            for child in node.get('children', []):
                output.append(process_node(child))
            if href:
                output.append('</a>')

        elif tag == 'span':
            is_spoiler = any(attr['key'] == 'class' and attr['value'] == 'md-spoiler-text' for attr in node.get('attrs', []))
            if is_spoiler:
                output.append('<tg-spoiler>')
                for child in node.get('children', []):
                    output.append(process_node(child))
                output.append('</tg-spoiler> ')
            else:
                for child in node.get('children', []):
                    output.append(process_node(child))

        elif tag in ['ul', 'ol']:
            for child in node.get('children', []):
                output.append(process_node(child))
            output.append('\n')

        elif tag == 'li':
            output.append('- ')
            for child in node.get('children', []):
                output.append(process_node(child))

        elif tag == 'hr':
            output.append('&#8213&#8213&#8213\n\n')

        else:
            for child in node.get('children', []):
                output.append(process_node(child))

    return ''.join(output)


class HTMLNodeAdapter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.root = {'type': 'root', 'children': []}
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = {
            'type': 'element',
            'data': tag,
            'attrs': [{'key': key, 'value': value} for key, value in attrs],
            'children': [],
            'parent': self.current
        }
        self.current['children'].append(node)
        self.stack.append(self.current)
        self.current = node

    def handle_endtag(self, tag):
        if self.stack:
            self.current = self.stack.pop()

    def handle_data(self, data):
        node = {
            'type': 'text',
            'data': data,
            'parent': self.current
        }
        self.current['children'].append(node)

    def get_parsed_tree(self):
        return self.root
