import logging

from fastapi import FastAPI

from src.mortgage.analyzer import MortgageLlmAnalyzer, MortgageTransparencyAnalyzer
from src.mortgage.content_validator import MortgageContentValidator
from src.mortgage.routes import router
from src.shared.events.analyzer_registry import register_analyzer, register_content_validator
from src.shared.infra.env.env import EnvSettings

logger = logging.getLogger(__name__)

FUND_TYPE = "mortgage"


def register_mortgage_module(app: FastAPI) -> None:
    env = EnvSettings()
    if env.gemini_api_key:
        analyzer = MortgageLlmAnalyzer(api_key=env.gemini_api_key, model=env.analysis_model)
        logger.info("Mortgage module using LLM analyzer (model=%s)", env.analysis_model)
    else:
        analyzer = MortgageTransparencyAnalyzer()
        logger.info("Mortgage module using heuristic analyzer (no GEMINI_API_KEY)")
    register_analyzer(FUND_TYPE, analyzer)
    register_content_validator(FUND_TYPE, MortgageContentValidator())
    app.include_router(router)
    logger.info("Mortgage module registered")
