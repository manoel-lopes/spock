import logging

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import analysis, funds, health, jobs
from src.infra.env.env_service import env_service

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
    version="1.0.0",
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

# Routes
app.include_router(health.router)
app.include_router(funds.router)
app.include_router(analysis.router)
app.include_router(jobs.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=env_service.port,
        reload=env_service.environment == "development",
    )
