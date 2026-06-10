from abc import ABC, abstractmethod

from core.domain.entity import Content


class Renderer(ABC):
    """Contract: convert Content to a platform-native message representation."""

    @abstractmethod
    def render(self, content: Content) -> str:
        ...

    @abstractmethod
    def render_with_link(self, content: Content) -> str:
        ...
