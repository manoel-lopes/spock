from src.shared.core.domain.entity import Entity


class Fund(Entity):
    ticker: str
    name: str
    fund_type: str = "equity"
    manager: str | None = None
    category: str | None = None
    source: str | None = None
    active: bool = True
