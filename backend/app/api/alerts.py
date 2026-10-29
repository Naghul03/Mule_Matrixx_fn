from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.alert import Alert
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.bank import Bank
from app.schemas.alert import AlertRead, AlertReviewRequest
from app.services.detection_service import DetectionService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertRead])
def list_alerts(
    domain: Optional[str] = Query(None),
    risk_band: Optional[str] = Query(None),
    scenario_run_id: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Alert).order_by(Alert.risk_score.desc(), Alert.created_at.desc())

    if domain:
        query = query.where(Alert.domain == domain)
    if risk_band:
        query = query.where(Alert.risk_band == risk_band)
    if scenario_run_id:
        query = query.where(Alert.scenario_run_id == scenario_run_id)
    if review_status:
        query = query.where(Alert.review_status == review_status)

    alerts = list(db.execute(query.limit(limit)).scalars().all())

    results = []
    for a in alerts:
        acc_ref = None
        bank_code = None
        if a.account_id:
            acc = db.get(Account, a.account_id)
            if acc:
                acc_ref = acc.display_alias or acc.bank_account_reference
                bank = db.get(Bank, acc.bank_id)
                if bank:
                    bank_code = bank.bank_code

        tx_ref = None
        if a.transaction_id:
            tx = db.get(Transaction, a.transaction_id)
            if tx:
                tx_ref = tx.native_transaction_reference

        results.append(
            AlertRead(
                id=a.id,
                domain=a.domain,
                scenario_run_id=a.scenario_run_id,
                account_id=a.account_id,
                transaction_id=a.transaction_id,
                account_ref=acc_ref,
                transaction_ref=tx_ref,
                bank_code=bank_code,
                risk_score=a.risk_score,
                risk_band=a.risk_band,
                signals=a.signals,
                detector_version=a.detector_version,
                review_status=a.review_status,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )
    return results


@router.post("/run-detection")
def run_detection(scenario_run_id: str, domain: str = "current_money", db: Session = Depends(get_db)):
    """Manually triggers detection engine over a scenario run."""
    svc = DetectionService(db)
    alerts = svc.analyze_scenario_run(scenario_run_id, domain)
    return {"message": f"Detection complete. Generated {len(alerts)} alerts.", "alerts_count": len(alerts)}


@router.post("/{alert_id}/review", response_model=AlertRead)
def review_alert(alert_id: str, req: AlertReviewRequest, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.review_status = req.review_status
    db.commit()
    db.refresh(alert)

    return AlertRead(
        id=alert.id,
        domain=alert.domain,
        scenario_run_id=alert.scenario_run_id,
        account_id=alert.account_id,
        transaction_id=alert.transaction_id,
        risk_score=alert.risk_score,
        risk_band=alert.risk_band,
        signals=alert.signals,
        detector_version=alert.detector_version,
        review_status=alert.review_status,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )

