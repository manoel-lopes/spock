from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from src.shared.infra.persistence.session import async_session_factory

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    db_status = await _check_database()

    status = "ok" if db_status["status"] == "up" else "degraded"

    return {
        "status": status,
        "timestamp": datetime.now(UTC).isoformat(),
        "db": db_status,
    }


async def _check_database() -> dict:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "up"}
    except Exception as e:
        return {"status": "down", "error": str(e)}
