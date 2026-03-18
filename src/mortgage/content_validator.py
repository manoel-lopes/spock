from src.shared.events.analyzer_registry import ContentValidator
from src.shared.domain.application.services.report_processor import PermanentFailure

_NON_REPORT_KEYWORDS = [
    "fato relevante",
    "comunicado ao mercado",
    "aviso aos cotistas",
]


class MortgageContentValidator(ContentValidator):
    def validate(self, text: str, page_count: int) -> None:
        """Reject documents that are not actual management reports."""

        lower = text.lower()
        if page_count <= 2:
            for keyword in _NON_REPORT_KEYWORDS:
                if keyword in lower[:500]:
                    raise PermanentFailure(
                        f"Document is not a management report (detected '{keyword}', {page_count} page(s))"
                    )
