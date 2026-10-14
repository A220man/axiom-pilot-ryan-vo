"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Health check")
async def health_check(settings=Depends(get_settings)) -> dict:
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/healthz/ready", summary="Readiness check")
async def readiness_check(
    db: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings),
) -> dict:
    """Readiness check including database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ready" if db_ok else "not_ready",
        "database": "connected" if db_ok else "disconnected",
        "app": settings.app_name,
        "version": settings.app_version,
    }