from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.main_router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info("Starting Mule Matrix API Backend [%s mode]", settings.ENVIRONMENT)
    logger.info("Database Target: %s", settings.sanitized_database_url)
    logger.info("Allowed CORS Origins: %s", settings.cors_origin_list)
    yield
    logger.info("Shutting down Mule Matrix API Backend")


def create_application() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Mule Matrix — Core Financial Intelligence API",
        description="Multi-Bank Money Muling Simulation, Detection & Investigation Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(api_router)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )

