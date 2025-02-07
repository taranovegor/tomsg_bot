import logging
import aiohttp

from core.analytics.analytics import Analytics, Events


class GoogleAnalytics(Analytics):
    """A class for logging events to Google Analytics via Measurement Protocol."""

    def __init__(self, measurement_id: str, secret: str, user_agent: str) -> None:
        """Initializes the GoogleAnalytics instance with measurement ID, secret, and user agent."""
        self.measurement_id = measurement_id
        self.secret = secret
        self.user_agent = user_agent

    async def log(self, events: Events) -> None:
        """Logs events to Google Analytics asynchronously."""
        body = {
            "user_id": events.get_user_id(),
            "client_id": events.get_user_id(),
            "events": list(
                map(
                    lambda ev: {
                        "name": ev.get_name(),
                        "params": ev,
                    },
                    events,
                )
            ),
        }

        url = f"https://www.google-analytics.com/mp/collect?measurement_id={self.measurement_id}&api_secret={self.secret}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    json=body,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": self.user_agent,
                    },
                ) as response:
                    response.raise_for_status()
            except aiohttp.ClientError as e:
                logging.error("Error sending data to Google Analytics: %s", e)
