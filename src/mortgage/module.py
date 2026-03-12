import logging

from fastapi import FastAPI

from src.mortgage.analyzer import MortgageTransparencyAnalyzer
from src.mortgage.content_validator import MortgageContentValidator
from src.mortgage.routes import router
from src.shared.events.analyzer_registry import register_analyzer, register_content_validator
from src.shared.events.event_bus import EventBus

logger = logging.getLogger(__name__)

FUND_TYPE = "mortgage"


def register_mortgage_module(app: FastAPI, event_bus: EventBus) -> None:
    register_analyzer(FUND_TYPE, MortgageTransparencyAnalyzer())
    register_content_validator(FUND_TYPE, MortgageContentValidator())
    app.include_router(router)
    logger.info("Mortgage module registered")
