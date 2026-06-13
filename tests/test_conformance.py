"""
Conformance tests: verify that platform adapters actually implement the ports.

A failure here means a class changed its signature or stopped inheriting
from the port — the DI wiring will break at runtime.
"""

from core.ports import Delivery, Renderer
from platforms.telegram.message import TelegramDelivery
from platforms.telegram.renderer import MessageRenderer


def test_message_renderer_is_renderer():
    assert issubclass(MessageRenderer, Renderer)
    assert isinstance(MessageRenderer(), Renderer)


def test_telegram_delivery_is_delivery():
    assert issubclass(TelegramDelivery, Delivery)
