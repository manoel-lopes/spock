from dataclasses import dataclass
from typing import Literal


@dataclass
class PaginationParams:
    page: int = 1
    page_size: int = 20
    order: Literal["asc", "desc"] = "desc"
