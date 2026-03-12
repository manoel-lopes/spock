import logging

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.equity.module import register_equity_module
from src.mortgage.module import register_mortgage_module
from src.shared.events.event_bus import EventBus
from src.shared.infra.env.env_service import env_service
from src.shared.infra.http.routes.health import router as health_router
from src.shared.workers.tasks.report_analysis import set_event_bus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

if env_service.sentry_dsn:
    sentry_sdk.init(
        dsn=env_service.sentry_dsn,
        environment=env_service.sentry_environment,
        traces_sample_rate=env_service.sentry_traces_sample_rate,
    )

app = FastAPI(
    title="Spock — FII Transparency Analysis",
    version="2.0.0",
    docs_url="/docs" if env_service.environment == "development" else None,
    redoc_url=None,
)

# CORS
if env_service.allowed_origins:
    origins = [o.strip() for o in env_service.allowed_origins.split(",") if o.strip()]
else:
    origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event bus
event_bus = EventBus()

# Set event bus on the worker module so Celery tasks can publish events
set_event_bus(event_bus)

# Register modules
register_equity_module(app, event_bus)
register_mortgage_module(app, event_bus)

# Health route (shared)
app.include_router(health_router)


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=env_service.port,
        reload=env_service.environment == "development",
    )
