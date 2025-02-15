import requests
import re
import json

from datetime import datetime

from core import (
    Parser as BaseParser,
    InvalidUrlError,
    ParseError,
    Content,
    Link,
)


class Parser(BaseParser):
    URL_REGEX = re.compile(r'^https://(?P<domain>dtf\.ru|vc\.ru)/[^?]+\?comment=(?P<comment_id>\d+)')
    REACTIONS_EMOJIS = {1: '❤️', 2: '🔥', 22: '😎', 4: '😂', 7: '😱', 3: '🥲', 5: '😡', 9: '🍿', 24: '👀', 10: '💸', 23: '😐', 41: '💊'}

    def __init__(self, user_agent: str):
        self.user_agent = user_agent

    def supports(self, url):
        return bool(self.URL_REGEX.match(url))

    def parse(self, string: str) -> Content:
        match = self.URL_REGEX.search(string)
        if not match:
            raise InvalidUrlError()

        domain = match.group('domain')
        comment_id = int(match.group('comment_id'))

        comments = self.__fetch(f'https://api.{domain}/v2.5/comments?commentId={comment_id}')
        comment = None
        for c in comments['result']['items']:
            if c['id'] == comment_id:
                comment = c
                break

        if comment is None:
            raise ParseError('comment not found in response')

        author_id = comment['author']['id']
        author_name = comment['author']['name']
        article_id = comment['entry']['id']
        article_title = comment['entry']['title']

        reactions = []
        for reaction in comment['reactions']['counters']:
            r_id = reaction['id']
            r_count = reaction['count']
            if r_count > 0 and r_id in self.REACTIONS_EMOJIS:
                reactions.append(f'{self.REACTIONS_EMOJIS[r_id]} {r_count}')

        return Content(
            author=Link(url=f'https://{domain}/u/{author_id}/', text=author_name),
            created_at=datetime.fromtimestamp(comment['date']),
            text=comment['text'],
            metrics=reactions,
            backlink=Link(url=f'https://{domain}/{article_id}?comment={comment_id}', text=article_title),
        )

    def __fetch(self, url):
        response = requests.get(url, headers={"User-Agent": self.user_agent})
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise ParseError(f'invalid status code {response.status_code}')
