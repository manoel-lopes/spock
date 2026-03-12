from abc import ABC, abstractmethod
from typing import Any


class UseCase(ABC):
    @abstractmethod
    async def execute(self, req: dict[str, Any]) -> Any:
        ...
