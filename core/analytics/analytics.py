import time

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Self


class Event(Dict[str, Any]):
    """Represents an individual event with a name and properties."""

    def __init__(self, name: str):
        """Initializes the event with a name."""
        super().__init__()
        self.name = name

    def get_name(self) -> str:
        """Returns the name of the event."""
        return self.name

    def add(self, prop: str, value: Any) -> Self:
        """Adds a property to the event."""
        self[prop] = value
        return self

    def get(self, prop: str) -> Any:
        """Returns the value of a specific property from the event."""
        return self[prop]


class Events(List[Event]):
    """Represents a collection of events associated with a user."""

    def __init__(self, user_id: str):
        """Initializes the events collection with a user ID and timestamp."""
        super().__init__()
        self.user_id = user_id
        self.created_at = self.__now_in_ms()

    def get_user_id(self) -> str:
        """Returns the user ID associated with the events."""
        return self.user_id

    def add(self, e: Event) -> Self:
        """Adds an event to the collection and tracks engagement time."""
        e.add("engagement_time_msec", self.__now_in_ms() - self.created_at + 1)
        self.append(e)
        return self

    @staticmethod
    def __now_in_ms() -> int:
        """Returns the current time in milliseconds."""
        return round(time.time() * 1000)


class Analytics(ABC):
    """Abstract base class for analytics services."""

    @abstractmethod
    async def log(self, events: Events) -> None:
        """Logs a collection of events as"""
        pass
