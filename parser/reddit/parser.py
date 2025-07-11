from html import unescape

import requests
import re
from typing import Dict, Any
from datetime import datetime, UTC

from core import (
    Parser as BaseParser,
    Content,
    Link,
    InvalidUrlError,
)
from parser.reddit.html_adapter import HTMLNodeAdapter, process_node


class Parser(BaseParser):
    SHORT_URL_REGEX = re.compile(
        r"https?://(?:www\.)?reddit\.com"
        r"/r/(?P<subreddit>[a-zA-Z0-9_]+)"
        r"/s/(?P<short_id>[a-zA-Z0-9]+)"
    )
    COMMENT_URL_REGEX = re.compile(
        r'^https://www\.reddit\.com/r/([a-zA-Z0-9_]+)/comments/([a-zA-Z0-9_]+)'
        r'(?:/[a-zA-Z0-9_%]+)?(?:/([a-zA-Z0-9_%]+))?/?(?:\?.*)?$'
    )

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.cache = {}

    def supports(self, url: str) -> bool:
        return any(pattern.match(url) for pattern in [
            self.SHORT_URL_REGEX,
            self.COMMENT_URL_REGEX,
        ])

    def parse(self, url: str) -> Content:
        access_token = self.get_auth_token()

        if self.SHORT_URL_REGEX.match(url):
            url = requests.get(url, headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": self.user_agent,
            }, allow_redirects=True).url

        matches = self.COMMENT_URL_REGEX.match(url)
        if not matches or len(matches.groups()) < 3:
            raise InvalidUrlError()

        comment_id = matches[3]

        data = self.fetch_reddit_comment(comment_id, access_token)
        return self.parse_reddit_comment(data)

    def get_auth_token(self) -> str:
        if 'access_token' in self.cache and self.cache['access_token']['expires_at'] > datetime.now().timestamp():
            return self.cache['access_token']['token']

        auth_url = "https://www.reddit.com/api/v1/access_token"
        data = {
            "grant_type": "client_credentials"
        }
        auth = (self.client_id, self.client_secret)
        headers = {"User-Agent": self.user_agent}

        response = requests.post(auth_url, data=data, auth=auth, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get auth token: {response.status_code} {response.text}")

        token_data = response.json()

        self.cache['access_token'] = {
            'token': token_data['access_token'],
            'expires_at': datetime.now().timestamp() + token_data['expires_in'] - 30,
        }

        return token_data['access_token']

    def fetch_reddit_comment(self, comment_id: str, access_token: str) -> Dict[str, Any]:
        api_url = f"https://www.reddit.com/api/info.json?id=t1_{comment_id}"
        headers = {
            "Authorization": f"{access_token}",
            "User-Agent": self.user_agent
        }

        response = requests.get(api_url, headers=headers, cookies={
            'reddit_session': access_token,
        })
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

        data = response.json()
        if not data['data']['children']:
            raise ValueError("No comments found in the response")

        return data['data']['children'][0]['data']

    def parse_reddit_comment(self, data: Dict[str, Any]) -> Content:
        return Content(
            author=Link(f"https://www.reddit.com/user/{data['author']}/", data['author']),
            created_at=datetime.fromtimestamp(data['created_utc'], UTC),
            text=self.strip_and_process_tags(data['body_html']),
            metrics=[f'⬆️ {data['ups']}', f'⬇️ {data['downs']}'],
            backlink=Link(f"https://www.reddit.com{data['permalink']}", self.extract_permalink_text(data['permalink'])),
        )

    @staticmethod
    def strip_and_process_tags(content: str):
        content = unescape(content.replace('\\n', '\n'))
        html_adapter = HTMLNodeAdapter()
        html_adapter.feed(content)

        output = []
        for child in html_adapter.get_parsed_tree().get('children', []):
            output.append(process_node(child))

        return ''.join(output).strip()

    @staticmethod
    def extract_permalink_text(permalink: str) -> str:
        match = re.match(r'^(/r/[^/]+?)/comments/[^/]+?/([^/]+?)/.*$', permalink)
        if match:
            return f"{match.group(1)}/{match.group(2)}/"
        return ""
