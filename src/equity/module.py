import logging

from fastapi import FastAPI

from src.equity.analyzer import EquityTransparencyAnalyzer
from src.equity.content_validator import EquityContentValidator
from src.equity.routes import router
from src.shared.events.analyzer_registry import register_analyzer, register_content_validator
from src.shared.events.event_bus import EventBus

logger = logging.getLogger(__name__)

FUND_TYPE = "equity"


def register_equity_module(app: FastAPI, event_bus: EventBus) -> None:
    register_analyzer(FUND_TYPE, EquityTransparencyAnalyzer())
    register_content_validator(FUND_TYPE, EquityContentValidator())
    app.include_router(router)
    logger.info("Equity module registered")
