import time

import aiohttp
import logging

from typing import Any, Dict, List


class Event(Dict[str, Any]):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def get_name(self) -> str:
        return self.name

    def add(self, prop: str, value: Any):
        self[prop] = value
        return self

    def get(self, prop: str) -> Any:
        return self[prop]


class Events(List[Event]):
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
        self.created_at = self.__now_in_ms()

    def get_user_id(self) -> str:
        return self.user_id

    def add(self, e: Event):
        e.add('engagement_time_msec', self.__now_in_ms() - self.created_at + 1)
        self.append(e)
        return self

    @staticmethod
    def __now_in_ms():
        return round(time.time() * 1000)


class Analytics:
    async def log(self, events: Events) -> None:
        raise NotImplementedError


class GoogleAnalytics(Analytics):
    def __init__(self, measurement_id: str, secret: str, user_agent: str) -> None:
        self.measurement_id = measurement_id
        self.secret = secret
        self.headers = {'Content-Type': 'application/json', 'User-Agent': user_agent}

    async def log(self, events: Events) -> None:
        body = {
            'user_id': events.get_user_id(),
            'client_id': events.get_user_id(),
            'events': list(map(lambda ev: {
                'name': ev.get_name(),
                'params': ev,
            }, events)),
        }

        url = f'https://www.google-analytics.com/mp/collect?measurement_id={self.measurement_id}&api_secret={self.secret}'
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=body, headers=self.headers) as response:
                    response.raise_for_status()
            except aiohttp.ClientError as e:
                logging.error('Error sending data to Google Analytics: %s', e)
