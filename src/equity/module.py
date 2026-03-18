import logging

from fastapi import FastAPI

from src.equity.analyzer import EquityLlmAnalyzer, EquityTransparencyAnalyzer
from src.equity.content_validator import EquityContentValidator
from src.equity.routes import router
from src.shared.events.analyzer_registry import register_analyzer, register_content_validator
from src.shared.infra.env.env import EnvSettings

logger = logging.getLogger(__name__)

FUND_TYPE = "equity"


def register_equity_module(app: FastAPI) -> None:
    env = EnvSettings()
    if env.gemini_api_key:
        analyzer = EquityLlmAnalyzer(api_key=env.gemini_api_key, model=env.analysis_model)
        logger.info("Equity module using LLM analyzer (model=%s)", env.analysis_model)
    else:
        analyzer = EquityTransparencyAnalyzer()
        logger.info("Equity module using heuristic analyzer (no GEMINI_API_KEY)")
    register_analyzer(FUND_TYPE, analyzer)
    register_content_validator(FUND_TYPE, EquityContentValidator())
    app.include_router(router)
    logger.info("Equity module registered")
