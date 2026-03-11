from src.core.domain.entity import Entity


class Fund(Entity):
    ticker: str
    name: str
    manager: str | None = None
    category: str | None = None
    source: str | None = None
    active: bool = True
