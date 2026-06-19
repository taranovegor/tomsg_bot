import time
from abc import ABC, abstractmethod
from typing import Any, Self


class Event:
    """Represents an individual event with a name and properties."""

    def __init__(self, name: str):
        self.name = name
        self._data: dict[str, Any] = {}

    def get_name(self) -> str:
        return self.name

    def add(self, prop: str, value: Any) -> Self:
        """Adds a property to the event."""
        self._data[prop] = value
        return self

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return repr(self._data)

    def items(self):
        return self._data.items()


class Events(list[Event]):
    """Represents a collection of events associated with a user."""

    def __init__(self, user_id: int, platform: str, handler_type: str):
        super().__init__()
        self.user_id = user_id
        self.platform = platform
        self.handler_type = handler_type
        self.created_at = self.__now_in_ms()

    def get_user_id(self) -> int:
        return self.user_id

    def add(self, e: Event) -> Self:
        """Adds an event to the collection and tracks engagement time."""
        e.add("platform", self.platform)
        e.add("handler_type", self.handler_type)
        e.add("engagement_time_msec", self.__now_in_ms() - self.created_at + 1)
        self.append(e)
        return self

    @staticmethod
    def __now_in_ms() -> int:
        return round(time.time() * 1000)


class Analytics(ABC):
    """Abstract base class for analytics services."""

    @abstractmethod
    async def log(self, events: Events) -> None:
        pass
