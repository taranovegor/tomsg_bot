import logging

import discord
from discord import app_commands

from platforms.discord.handler import DiscordMessageHandler


class DiscordBot:
    """Discord transport: gateway connection, slash command, and message listener.

    Trigger model (no inline-query equivalent):
    - Slash command ``/tomsg <url>`` for explicit expansion.
    - Auto-detection of link-only messages.
    """

    def __init__(self, token: str, handler: DiscordMessageHandler):
        self.token = token
        self.handler = handler
        self._message_content_ok = True
        self._synced = False

        self._build_client()

    def _build_client(self) -> None:
        intents = discord.Intents.default()
        if self._message_content_ok:
            intents.message_content = True
        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)

        self._register_events()
        self._register_commands()

    def _register_events(self) -> None:
        @self.client.event
        async def on_ready() -> None:
            logging.info(
                "Discord bot logged in as %s (ID: %s)",
                self.client.user,
                self.client.user.id if self.client.user else "?",
            )
            if not self._message_content_ok:
                logging.info(
                    "Message content intent not available — slash command /tomsg works, "
                    "auto-detection of links in messages requires enabling "
                    "'Message Content Intent' in the Discord Developer Portal"
                )
            if not self._synced:
                await self.tree.sync()
                self._synced = True

        @self.client.event
        async def on_message(message: discord.Message) -> None:
            if not self._message_content_ok:
                return
            if message.author.bot:
                return
            await self.handler.handle_message(message)

    def _register_commands(self) -> None:
        @self.tree.command(
            name="tomsg",
            description="Expand a social-media link into a readable message",
        )
        @app_commands.describe(url="The link to expand")
        async def tomsg(interaction: discord.Interaction, url: str) -> None:
            await self.handler.handle_slash(interaction, url)

    def run(self) -> None:
        """Start the Discord gateway connection (blocking).

        Falls back gracefully if the ``message_content`` privileged intent
        is not enabled in the Discord Developer Portal — the slash command
        still works; only auto-detection of links is skipped.
        """
        try:
            self.client.run(self.token, log_handler=None)
        except discord.PrivilegedIntentsRequired:
            if not self._message_content_ok:
                raise
            logging.warning(
                "Message Content intent not granted — rebuilding without it. "
                "Slash command /tomsg will still work."
            )
            self._message_content_ok = False
            self._build_client()
            self.client.run(self.token, log_handler=None)
