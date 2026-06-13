from abc import ABC, abstractmethod

from core.domain import PipelineResult


class Delivery(ABC):
    """Contract: deliver resolved content (Content + local files) to platform target."""

    @abstractmethod
    async def send(self, target, result: PipelineResult) -> None: ...
