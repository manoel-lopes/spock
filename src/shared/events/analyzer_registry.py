import logging

from src.shared.infra.adapters.analysis.ports.transparency_analyzer import (
    TransparencyAnalyzer,
)

logger = logging.getLogger(__name__)

_analyzers: dict[str, TransparencyAnalyzer] = {}

_content_validators: dict[str, "ContentValidator"] = {}


class ContentValidator:
    """Base class for module-specific content validators."""

    def validate(self, text: str, page_count: int) -> None:
        """Raise PermanentFailure if the document should be rejected."""


def register_analyzer(fund_type: str, analyzer: TransparencyAnalyzer) -> None:
    _analyzers[fund_type] = analyzer
    logger.info("Registered analyzer for fund_type='%s'", fund_type)


def get_analyzer(fund_type: str) -> TransparencyAnalyzer:
    analyzer = _analyzers.get(fund_type)
    if not analyzer:
        raise ValueError(f"No analyzer registered for fund_type='{fund_type}'")
    return analyzer


def register_content_validator(fund_type: str, validator: ContentValidator) -> None:
    _content_validators[fund_type] = validator
    logger.info("Registered content validator for fund_type='%s'", fund_type)


def get_content_validator(fund_type: str) -> ContentValidator:
    return _content_validators.get(fund_type, ContentValidator())
