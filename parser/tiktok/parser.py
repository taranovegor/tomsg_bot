import re
import requests

from core.parser import Parser as BaseParser, Video, UnableToParse, Link


class Parser(BaseParser):
    SHORT_URL_REGEX = re.compile(r"^https://vm\.tiktok\.com/(?P<video_id>\w+)/?(\?.*)?$")
    FULL_URL_REGEX = re.compile(r"^https://(?:www|m\.)?tiktok\.com/(?:@[^/]*/video/|v/)(?P<video_id>\d+)(?:\.html)?/?(\?.*)?$")

    def __init__(self, video_resource_url: str, thumbnail_resource_url: str, user_agent: str):
        self.video_resource_url = video_resource_url
        self.thumbnail_resource_url = thumbnail_resource_url
        self.user_agent = user_agent

    def supports(self, url: str) -> bool:
        return any(pattern.match(url) for pattern in [
            self.SHORT_URL_REGEX,
            self.FULL_URL_REGEX,
        ])

    def parse(self, url: str) -> Video:
        if self.SHORT_URL_REGEX.match(url):
            response = requests.head(url, headers={'User-Agent': self.user_agent})
            print(response.headers)
            long_url_match = self.FULL_URL_REGEX.match(response.headers.get('Location'))
        else:
            long_url_match = self.FULL_URL_REGEX.match(url)

        if long_url_match:
            video_id = long_url_match.group('video_id')
        else:
            raise UnableToParse('Unprocessable link')

        return Video(
            resource_url=self.video_resource_url % video_id,
            mime_type='video/mp4',
            thumbnail_url=self.thumbnail_resource_url % video_id,
            backlink=Link(f'https://tiktok.com/@/video/{video_id}', ''),
        )
