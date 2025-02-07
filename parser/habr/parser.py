import requests
import re
import json

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from core import Parser as BaseParser, ParseError, Content, Link
from parser.habr.html_processor import HTMLProcessor


class Parser(BaseParser):
    def __init__(self, user_agent: str):
        self.user_agent = user_agent

    def supports(self, url):
        return "habr.com" in url and "#comment_" in url

    def parse(self, string: str) -> Content:
        match = re.search(r"/articles/(\d+)/#comment_(\d+)", string)
        if not match:
            raise ParseError('comment not found')

        article_id = match.group(1)
        with ThreadPoolExecutor() as executor:
            article_future = executor.submit(self.__fetch, f'https://habr.com/kek/v2/articles/{article_id}/')
            comments_future = executor.submit(self.__fetch,f'https://habr.com/kek/v2/articles/{article_id}/comments/split/guest/')

            article = article_future.result()
            comments = comments_future.result()

        article_title = article['titleHtml']
        comments = comments['commentRefs']

        comment_id = match.group(2)
        if not comment_id in comments:
            raise ParseError('comment not found')
        comment = comments[comment_id]
        author = comment['author']['alias']

        return Content(
            author=Link(url=f'https://habr.com/ru/users/{author}/', text=author),
            created_at=datetime.fromisoformat(comment['timePublished']),
            text=HTMLProcessor().process(comment['message']),
            metrics=[],
            backlink=Link(url=f'https://habr.com/ru/articles/{article_id}/#comment_{comment_id}', text=article_title),
        )

    def __fetch(self, url):
        response = requests.get(url, headers={"User-Agent": self.user_agent})
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise ParseError
