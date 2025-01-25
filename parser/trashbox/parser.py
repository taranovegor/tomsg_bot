import pytz
import requests
import re
import json

from urllib.parse import urlparse
from html import unescape
from datetime import datetime

from core.parser import UnableToParse, Text, Link
from core.parser import Parser as BaseParser


def find_comment_by_id(comments, comment_id):
    for comment in comments:
        if comment['comm_id'] == comment_id:
            return comment
    return None


def replace_img(match):
    src = match.group(1)
    return f'<a href="https://trashbox.ru/{src.lstrip("/")}">🖼 Изображение</a>'


def format_content(content):
    img_re = re.compile('<img[^>]*src=["\'](.*?)["\'][^>]*>')
    content = img_re.sub(replace_img, content)

    content = content.replace("<br/>", "\n")
    content = content.replace("<li>", "- ")
    content = content.replace("</li>", "\n")

    return unescape(content)


class Parser(BaseParser):
    def __init__(self, user_agent: str):
        self.user_agent = user_agent

    def supports(self, url):
        return "trashbox.ru" in url and "#div_comment_" in url

    def parse(self, string: str) -> Text:
        link_data = self.__parse_topic(string)

        comments = self.fetch_comments(link_data['topic_id'])
        comment = find_comment_by_id(comments, link_data['comment_id'])
        if comment is None:
            raise UnableToParse

        return Text(
            author=Link(url=f'https://trashbox.ru/users/{comment["login"]}/', text=comment['login']),
            created_at=datetime.fromtimestamp(int(comment['posted'])).astimezone(pytz.timezone("Europe/Moscow")),
            content=format_content(comment['content']),
            metrics=[f'👍 {comment["votes1"]}', f'👎 {comment["votes0"].lstrip("-")}'],
            backlink=Link(url=string, text=link_data['title']),
        )

    def __parse_topic(self, url: str):
        parsed_url = urlparse(url)
        segments = parsed_url.path.split("/")
        if len(segments) < 3 or not url.startswith("https://trashbox.ru"):
            raise UnableToParse

        topic_id = segments[2]

        frag_parts = parsed_url.fragment.split("_")
        if len(frag_parts) < 3:
            raise UnableToParse

        comment_id = frag_parts[2]

        body = self.fetch(f'https://trashbox.ru/api_topics/{topic_id}')

        topic_match = re.search(r'<trashTopicId>([0-9]*)</trashTopicId>', body)
        title_match = re.findall(r'<!\[CDATA\[(.*?)]]>', body)

        if not topic_match or not title_match:
            raise UnableToParse('Failed to parse topic')

        return {
            'topic_id': topic_match.group(1),
            'comment_id': comment_id,
            'title': title_match[1],
        }

    def fetch_comments(self, topic_id):
        return json.loads(self.fetch(f'https://trashbox.ru/api_noauth.php?action=comments&topic_id={topic_id}'))['comments']

    def fetch(self, url) -> str:
        response = requests.get(url, headers={"User-Agent": self.user_agent})
        if response.status_code == 200:
            return response.text
        else:
            raise UnableToParse
