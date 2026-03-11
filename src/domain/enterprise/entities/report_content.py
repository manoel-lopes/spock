from src.core.domain.entity import Entity


class ReportContent(Entity):
    report_id: str
    raw_text: str
    normalized_text: str | None = None
    page_count: int
    parser_version: str | None = None
