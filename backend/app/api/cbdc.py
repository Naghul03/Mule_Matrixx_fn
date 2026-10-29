from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.cbdc import CBDCWallet, CBDCTokenLot, CBDCLedgerEvent
from app.schemas.cbdc import (
    CBDCWalletRead,
    CBDCTokenLotRead,
    CBDCLedgerEventRead,
    CBDCProvenanceResponse,
)
from app.services.cbdc_service import CBDCService

router = APIRouter(prefix="/cbdc", tags=["CBDC"])


@router.get("/wallets", response_model=List[CBDCWalletRead])
def list_wallets(db: Session = Depends(get_db)):
    wallets = list(db.execute(select(CBDCWallet).order_by(CBDCWallet.balance.desc())).scalars().all())
    return [
        CBDCWalletRead(
            id=w.id,
            wallet_address=w.wallet_address,
            display_name=w.display_name,
            wallet_type=w.wallet_type,
            balance=w.balance,
            synthetic_classification=w.synthetic_classification,
            is_active=w.is_active,
            created_at=w.created_at,
        )
        for w in wallets
    ]


@router.get("/lots", response_model=List[CBDCTokenLotRead])
def list_token_lots(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    query = select(CBDCTokenLot).order_by(CBDCTokenLot.created_at.desc())
    if status_filter:
        query = query.where(CBDCTokenLot.status == status_filter)
    lots = list(db.execute(query.limit(50)).scalars().all())
    return [
        CBDCTokenLotRead(
            id=l.id,
            lot_reference=l.lot_reference,
            current_holder_wallet_id=l.current_holder_wallet_id,
            amount=l.amount,
            currency=l.currency,
            status=l.status,
            created_at=l.created_at,
        )
        for l in lots
    ]


@router.get("/events", response_model=List[CBDCLedgerEventRead])
def list_ledger_events(
    scenario_run_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(CBDCLedgerEvent).order_by(CBDCLedgerEvent.event_timestamp.desc())
    if scenario_run_id:
        query = query.where(CBDCLedgerEvent.scenario_run_id == scenario_run_id)

    events = list(db.execute(query.limit(limit)).scalars().all())

    results = []
    for e in events:
        from_w = db.get(CBDCWallet, e.from_wallet_id) if e.from_wallet_id else None
        to_w = db.get(CBDCWallet, e.to_wallet_id)

        results.append(
            CBDCLedgerEventRead(
                id=e.id,
                scenario_run_id=e.scenario_run_id,
                event_type=e.event_type,
                from_wallet_id=e.from_wallet_id,
                to_wallet_id=e.to_wallet_id,
                from_wallet_address=from_w.wallet_address if from_w else None,
                to_wallet_address=to_w.wallet_address if to_w else "UNKNOWN",
                amount=e.amount,
                currency=e.currency,
                event_timestamp=e.event_timestamp,
                parent_lot_ids=e.parent_lot_ids,
                child_lot_ids=e.child_lot_ids,
                metadata_json=e.metadata_json,
            )
        )
    return results


@router.get("/provenance/{lot_ref}", response_model=CBDCProvenanceResponse)
def get_token_provenance(lot_ref: str, db: Session = Depends(get_db)):
    svc = CBDCService(db)
    try:
        return svc.get_token_provenance(lot_ref)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.post("/scenarios/run", status_code=status.HTTP_201_CREATED)
def run_cbdc_scenario(
    seed: int = Query(42),
    amount: Optional[Decimal] = Query(None),
    db: Session = Depends(get_db),
):
    """Executes CBDC Scenario 2: Token lot minting, splitting, peeling transfer, and merge."""
    svc = CBDCService(db)
    run = svc.generate_scenario_2(seed=seed, base_amount=amount)
    return {
        "message": "CBDC Scenario 2 executed successfully",
        "scenario_run_id": run.id,
        "seed": run.seed,
        "status": run.status,
    }

