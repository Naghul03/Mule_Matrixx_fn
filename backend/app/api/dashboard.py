from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.case import Case
from app.db.models.alert import Alert
from app.db.models.scenario_run import ScenarioRun
from app.db.models.transaction import Transaction
from app.db.models.cbdc import CBDCLedgerEvent
from app.schemas.dashboard import DashboardMetricsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    domain: str = Query("current_money", description="current_money or cbdc"),
    db: Session = Depends(get_db),
):
    """Computes operational metrics strictly from persisted records.
    Never mixes Current Money and CBDC statistics.
    """
    # 1. Cases Counts
    total_cases = db.execute(select(func.count(Case.id)).where(Case.domain == domain)).scalar() or 0
    open_cases = db.execute(
        select(func.count(Case.id)).where(Case.domain == domain, Case.status == "OPEN")
    ).scalar() or 0
    escalated_cases = db.execute(
        select(func.count(Case.id)).where(Case.domain == domain, Case.status == "ESCALATED")
    ).scalar() or 0

    # 2. Alerts by Risk Band
    high_alerts = db.execute(
        select(func.count(Alert.id)).where(Alert.domain == domain, Alert.risk_band == "HIGH")
    ).scalar() or 0
    med_alerts = db.execute(
        select(func.count(Alert.id)).where(Alert.domain == domain, Alert.risk_band == "MEDIUM")
    ).scalar() or 0
    low_alerts = db.execute(
        select(func.count(Alert.id)).where(Alert.domain == domain, Alert.risk_band == "LOW")
    ).scalar() or 0

    # 3. Transactions / Events and Volume
    if domain == "current_money":
        total_txns = db.execute(select(func.count(Transaction.id))).scalar() or 0
        total_vol = db.execute(select(func.sum(Transaction.amount))).scalar() or Decimal("0")
    else:
        total_txns = db.execute(select(func.count(CBDCLedgerEvent.id))).scalar() or 0
        total_vol = db.execute(select(func.sum(CBDCLedgerEvent.amount))).scalar() or Decimal("0")

    # 4. Recent Scenario Runs
    recent_runs = list(
        db.execute(
            select(ScenarioRun)
            .where(ScenarioRun.domain == domain)
            .order_by(ScenarioRun.created_at.desc())
            .limit(5)
        ).scalars().all()
    )
    runs_data = [
        {
            "id": r.id,
            "scenario": r.scenario_identifier,
            "seed": r.seed,
            "status": r.status,
            "createdAt": r.created_at.isoformat(),
        }
        for r in recent_runs
    ]

    # 5. Recent Alerts
    recent_alerts = list(
        db.execute(
            select(Alert)
            .where(Alert.domain == domain)
            .order_by(Alert.created_at.desc())
            .limit(5)
        ).scalars().all()
    )
    alerts_data = [
        {
            "id": a.id,
            "riskScore": float(a.risk_score),
            "riskBand": a.risk_band,
            "signalsCount": len(a.signals),
            "createdAt": a.created_at.isoformat(),
        }
        for a in recent_alerts
    ]

    return DashboardMetricsResponse(
        domain=domain,
        total_cases=total_cases,
        open_cases=open_cases,
        escalated_cases=escalated_cases,
        high_risk_alerts=high_alerts,
        medium_risk_alerts=med_alerts,
        low_risk_alerts=low_alerts,
        total_transactions=total_txns,
        total_volume=float(total_vol),
        recent_scenario_runs=runs_data,
        recent_alerts=alerts_data,
    )

