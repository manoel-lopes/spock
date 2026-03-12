from dataclasses import dataclass, field
from math import ceil


@dataclass
class PaginatedItems[T]:
    items: list[T]
    page: int
    page_size: int
    total_items: int
    order: str = "desc"
    total_pages: int = field(init=False)

    def __post_init__(self) -> None:
        self.total_pages = max(1, ceil(self.total_items / self.page_size))
