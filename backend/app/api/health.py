import time
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, DatabaseHealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def get_service_health() -> HealthResponse:
    """Basic service health check."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="mule-matrix-backend",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )


@router.get("/database", response_model=DatabaseHealthResponse)
def get_database_health(db: Session = Depends(get_db)):
    """Database connectivity health check.
    Executes a lightweight query (SELECT 1) and measures latency.
    Credentials and connection strings are strictly redacted.
    """
    settings = get_settings()
    start_time = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return DatabaseHealthResponse(
            status="connected",
            database=settings.DB_NAME,
            latency_ms=latency_ms,
            error=None,
        )
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        sanitized_error = f"Database connectivity check failed: {type(exc).__name__}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=DatabaseHealthResponse(
                status="disconnected",
                database=settings.DB_NAME,
                latency_ms=latency_ms,
                error=sanitized_error,
            ).model_dump(),
        )

