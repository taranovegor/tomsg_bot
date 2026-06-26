import asyncio
import logging
from urllib.parse import urlparse

from core.exceptions import InvalidUrlError, ParserNotFoundError
from core.pipeline import Pipeline
from core.ports.delivery import Delivery
from infra.analytics.analytics import Analytics, Event, Events
from platforms.discord.i18n import t
from shared.urls import is_valid_url


class DiscordMessageHandler:
    """
    Process URLs from Discord messages: validate, run neutral pipeline,
    and dispatch result to DiscordDelivery.

    Trigger model (no inline-query equivalent):
    - Slash command `/tomsg <url>` (explicit).
    - Auto-detect link-only messages (implicit).
    """

    def __init__(
        self,
        pipeline: Pipeline,
        delivery: Delivery,
        analytics: Analytics,
        platform: str = "discord",
    ):
        self.pipeline = pipeline
        self.delivery = delivery
        self.analytics = analytics
        self.platform = platform

    async def handle_url(
        self,
        url: str,
        target,
        user_id: int | None = None,
        locale: str | None = None,
        *,
        wait_delivery: bool = False,
    ) -> None:
        events = Events(user_id or 0, self.platform, "message")

        async def _send_error(text: str) -> None:
            try:
                await target.send(text, suppress_embeds=True)
            except TypeError:
                await target.send(text)

        try:
            if not is_valid_url(url):
                raise InvalidUrlError()

            result = await self.pipeline.run(url)
            events.add(Event("page_view").add("page_location", url))
            task = asyncio.create_task(self.delivery.send(target, result))

            if wait_delivery:
                await task
            else:
                task.add_done_callback(self._log_task_exception)

        except asyncio.CancelledError:
            raise
        except InvalidUrlError as e:
            logging.warning("Invalid URL received: %s", url)
            events.add(Event("exception").add("description", str(e)).add("type", type(e).__name__))
            await _send_error(t("invalid_url", locale))
        except ParserNotFoundError as e:
            hostname = urlparse(url).netloc
            logging.warning("Parser not found for hostname: %s", hostname)
            events.add(
                Event("exception")
                .add("description", str(e))
                .add("type", type(e).__name__)
                .add("hostname", hostname)
            )
            await _send_error(t("parser_not_found", locale).format(hostname=hostname))
        except Exception as e:
            logging.error("Exception while processing URL: %s", url, exc_info=True)
            events.add(Event("exception").add("description", str(e)).add("type", type(e).__name__))
            await _send_error(t("exception", locale))

        await self.analytics.log(events)

    async def handle_message(self, message) -> None:
        """Auto-detect URL in a Discord message and respond.

        Locale is not available for on_message — discord.User/Member has no
        ``locale`` attribute (only Interaction does). Always falls back to
        the default locale.
        """
        if not message.content:
            return
        url = message.content.strip()
        if not is_valid_url(url):
            return
        await self.handle_url(url, message.channel, message.author.id)

    async def handle_slash(self, interaction, url: str) -> None:
        """Handle a /tomsg <url> slash command."""
        locale = str(interaction.locale) if hasattr(interaction, "locale") else None
        await interaction.response.defer()
        await self.handle_url(
            url,
            interaction.followup,
            interaction.user.id,
            locale,
            wait_delivery=True,
        )

    @staticmethod
    def _log_task_exception(task: asyncio.Task) -> None:
        if not task.cancelled() and (exc := task.exception()):
            logging.error("Background send task failed", exc_info=exc)
