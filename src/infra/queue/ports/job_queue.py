from abc import ABC, abstractmethod
from typing import Any


class JobQueue(ABC):
    @abstractmethod
    async def add(self, name: str, data: dict[str, Any]) -> str: ...

    @abstractmethod
    async def get_status(self, job_id: str) -> str | None: ...
