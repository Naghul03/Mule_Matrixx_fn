from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.transaction import Transaction
from app.db.models.account import Account
from app.db.models.bank import Bank

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
def list_transactions(
    scenario_run_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    bank_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieves normalized canonical transactions.
    STRICT PRIVACY: Never joins with ground_truth_labels.
    """
    query = select(Transaction).order_by(Transaction.event_timestamp.desc())

    if scenario_run_id:
        query = query.where(Transaction.scenario_run_id == scenario_run_id)
    if account_id:
        query = query.where(
            (Transaction.source_account_id == account_id)
            | (Transaction.destination_account_id == account_id)
        )
    if bank_id:
        query = query.where(Transaction.originating_bank_id == bank_id)

    txns = list(db.execute(query.limit(limit).offset(offset)).scalars().all())

    results = []
    for t in txns:
        src = db.get(Account, t.source_account_id)
        dst = db.get(Account, t.destination_account_id)
        bank = db.get(Bank, t.originating_bank_id)

        results.append({
            "id": t.id,
            "scenario_run_id": t.scenario_run_id,
            "originating_bank": {
                "id": bank.id if bank else None,
                "code": bank.bank_code if bank else "UNKNOWN",
                "name": bank.display_name if bank else "Unknown Bank",
            },
            "source_account": {
                "id": src.id if src else None,
                "reference": src.bank_account_reference if src else "UNKNOWN",
                "alias": src.display_alias if src else None,
            },
            "destination_account": {
                "id": dst.id if dst else None,
                "reference": dst.bank_account_reference if dst else "UNKNOWN",
                "alias": dst.display_alias if dst else None,
            },
            "amount": float(t.amount),
            "currency": t.currency,
            "event_timestamp": t.event_timestamp.isoformat(),
            "native_reference": t.native_transaction_reference,
            "normalized_type": t.normalized_type,
            "status": t.status,
            "source_adapter_version": t.source_adapter_version,
            "created_at": t.created_at.isoformat(),
        })

    return results


@router.get("/{txn_id}")
def get_transaction(txn_id: str, db: Session = Depends(get_db)):
    t = db.get(Transaction, txn_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")

    src = db.get(Account, t.source_account_id)
    dst = db.get(Account, t.destination_account_id)
    bank = db.get(Bank, t.originating_bank_id)

    return {
        "id": t.id,
        "scenario_run_id": t.scenario_run_id,
        "originating_bank": {
            "id": bank.id if bank else None,
            "code": bank.bank_code if bank else "UNKNOWN",
            "name": bank.display_name if bank else "Unknown Bank",
        },
        "source_account": {
            "id": src.id if src else None,
            "reference": src.bank_account_reference if src else "UNKNOWN",
            "alias": src.display_alias if src else None,
        },
        "destination_account": {
            "id": dst.id if dst else None,
            "reference": dst.bank_account_reference if dst else "UNKNOWN",
            "alias": dst.display_alias if dst else None,
        },
        "amount": float(t.amount),
        "currency": t.currency,
        "event_timestamp": t.event_timestamp.isoformat(),
        "native_reference": t.native_transaction_reference,
        "normalized_type": t.normalized_type,
        "status": t.status,
        "source_adapter_version": t.source_adapter_version,
        "raw_payload": t.raw_payload,
        "normalization_metadata": t.normalization_metadata,
        "created_at": t.created_at.isoformat(),
    }

