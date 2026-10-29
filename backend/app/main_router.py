from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.scenarios import router as scenarios_router
from app.api.transactions import router as transactions_router
from app.api.alerts import router as alerts_router
from app.api.cases import router as cases_router
from app.api.investigation import router as investigation_router
from app.api.evaluation import router as evaluation_router
from app.api.cbdc import router as cbdc_router
from app.api.reports import router as reports_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(scenarios_router)
api_router.include_router(transactions_router)
api_router.include_router(alerts_router)
api_router.include_router(cases_router)
api_router.include_router(investigation_router)
api_router.include_router(evaluation_router)
api_router.include_router(cbdc_router)
api_router.include_router(reports_router)
api_router.include_router(dashboard_router)
