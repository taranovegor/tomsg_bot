import logging
import aiohttp

from core.analytics.analytics import Analytics, Events


class GoogleAnalytics(Analytics):
    """
    A class for logging events to Google Analytics via Measurement Protocol.
    """

    def __init__(
        self,
        measurement_id: str,
        secret: str,
        user_agent: str,
        mask_identifier: lambda: str,
    ) -> None:
        """Initializes the GA instance."""
        self.measurement_id = measurement_id
        self.secret = secret
        self.user_agent = user_agent
        self.mask_identifier = mask_identifier

    async def log(self, events: Events) -> None:
        """Logs events to GA asynchronously."""
        user_id = self.mask_identifier(events.get_user_id())
        payload = {
            "user_id": user_id,
            "client_id": user_id,
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

        logging.debug(
            "Sending data to GA: measurement_id=%s, payload=%s",
            self.measurement_id,
            payload,
        )

        url = (
            f"https://www.google-analytics.com/mp/collect"
            f"?measurement_id={self.measurement_id}"
            f"&api_secret={self.secret}"
        )
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": self.user_agent,
                    },
                ) as response:
                    response.raise_for_status()
                    logging.debug(
                        "Successfully sent data to GA. Status: %d",
                        response.status,
                    )
            except aiohttp.ClientError as e:
                logging.error(
                    "Error sending data to GA: %s",
                    e,
                    exc_info=True,
                )
