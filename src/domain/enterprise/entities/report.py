from datetime import datetime

from src.core.domain.entity import Entity


class Report(Entity):
    fund_id: str
    reference_month: datetime
    publication_date: datetime | None = None
    pdf_url: str
    pdf_hash: str | None = None
    status: str = "pending"
    error_message: str | None = None
