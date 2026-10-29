from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.case import Case, CaseAlert, CaseAccount, CaseTransaction, CaseNote
from app.db.models.alert import Alert
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.bank import Bank
from app.schemas.case import (
    CaseRead,
    CaseDetail,
    CaseStatusUpdateRequest,
    ManualCaseCreateRequest,
)

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("", response_model=List[CaseRead])
def list_cases(
    domain: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    risk_band: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Case).order_by(Case.created_at.desc())

    if domain:
        query = query.where(Case.domain == domain)
    if status_filter:
        query = query.where(Case.status == status_filter)
    if priority:
        query = query.where(Case.priority == priority)
    if risk_band:
        query = query.where(Case.risk_band == risk_band)
    if search:
        query = query.where(
            (Case.case_reference.ilike(f"%{search}%"))
            | (Case.title.ilike(f"%{search}%"))
            | (Case.summary.ilike(f"%{search}%"))
        )

    cases = list(db.execute(query.limit(limit)).scalars().all())

    results = []
    for c in cases:
        al_count = db.execute(select(func.count(CaseAlert.id)).where(CaseAlert.case_id == c.id)).scalar() or 0
        acc_count = db.execute(select(func.count(CaseAccount.id)).where(CaseAccount.case_id == c.id)).scalar() or 0
        tx_count = db.execute(select(func.count(CaseTransaction.id)).where(CaseTransaction.case_id == c.id)).scalar() or 0

        results.append(
            CaseRead(
                id=c.id,
                case_reference=c.case_reference,
                domain=c.domain,
                title=c.title,
                summary=c.summary,
                status=c.status,
                priority=c.priority,
                risk_band=c.risk_band,
                aggregate_risk_score=c.aggregate_risk_score,
                scenario_run_id=c.scenario_run_id,
                is_manual_entry=c.is_manual_entry,
                manual_entry_data=c.manual_entry_data,
                created_at=c.created_at,
                updated_at=c.updated_at,
                alert_count=al_count,
                account_count=acc_count,
                transaction_count=tx_count,
            )
        )
    return results


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    # Load linked Alerts
    case_alerts = list(
        db.execute(select(CaseAlert).where(CaseAlert.case_id == c.id)).scalars().all()
    )
    alerts_data = []
    for ca in case_alerts:
        a = db.get(Alert, ca.alert_id)
        if a:
            alerts_data.append({
                "id": a.id,
                "risk_score": float(a.risk_score),
                "risk_band": a.risk_band,
                "signals": a.signals,
                "review_status": a.review_status,
                "created_at": a.created_at.isoformat(),
            })

    # Load linked Accounts
    case_accs = list(
        db.execute(select(CaseAccount).where(CaseAccount.case_id == c.id)).scalars().all()
    )
    accs_data = []
    for ca in case_accs:
        acc = db.get(Account, ca.account_id)
        if acc:
            bank = db.get(Bank, acc.bank_id)
            accs_data.append({
                "id": acc.id,
                "reference": acc.bank_account_reference,
                "alias": acc.display_alias,
                "bank_code": bank.bank_code if bank else "UNKNOWN",
                "role": ca.role,
            })

    # Load linked Transactions
    case_txns = list(
        db.execute(select(CaseTransaction).where(CaseTransaction.case_id == c.id)).scalars().all()
    )
    txns_data = []
    for ct in case_txns:
        t = db.get(Transaction, ct.transaction_id)
        if t:
            src = db.get(Account, t.source_account_id)
            dst = db.get(Account, t.destination_account_id)
            txns_data.append({
                "id": t.id,
                "reference": t.native_transaction_reference,
                "source": src.bank_account_reference if src else "UNKNOWN",
                "destination": dst.bank_account_reference if dst else "UNKNOWN",
                "amount": float(t.amount),
                "currency": t.currency,
                "timestamp": t.event_timestamp.isoformat(),
                "evidence_type": ct.evidence_type,
            })

    # Load Notes & Audit History
    notes = list(
        db.execute(
            select(CaseNote).where(CaseNote.case_id == c.id).order_by(CaseNote.created_at.desc())
        ).scalars().all()
    )
    notes_data = [
        {
            "id": n.id,
            "note_type": n.note_type,
            "content": n.content,
            "previous_status": n.previous_status,
            "new_status": n.new_status,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]

    return CaseDetail(
        id=c.id,
        case_reference=c.case_reference,
        domain=c.domain,
        title=c.title,
        summary=c.summary,
        status=c.status,
        priority=c.priority,
        risk_band=c.risk_band,
        aggregate_risk_score=c.aggregate_risk_score,
        scenario_run_id=c.scenario_run_id,
        is_manual_entry=c.is_manual_entry,
        manual_entry_data=c.manual_entry_data,
        created_at=c.created_at,
        updated_at=c.updated_at,
        alert_count=len(alerts_data),
        account_count=len(accs_data),
        transaction_count=len(txns_data),
        alerts=alerts_data,
        accounts=accs_data,
        transactions=txns_data,
        notes=notes_data,
    )


@router.put("/{case_id}/status", response_model=CaseDetail)
def update_case_status(case_id: str, req: CaseStatusUpdateRequest, db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    old_status = c.status
    c.status = req.status
    c.updated_at = datetime.now(timezone.utc)

    # Persist audit note
    note = CaseNote(
        id=str(uuid.uuid4()),
        case_id=c.id,
        note_type="STATUS_CHANGE",
        content=req.note,
        previous_status=old_status,
        new_status=req.status,
    )
    db.add(note)
    db.commit()

    return get_case(case_id, db)


@router.post("/manual", response_model=CaseDetail, status_code=status.HTTP_201_CREATED)
def create_manual_case(req: ManualCaseCreateRequest, db: Session = Depends(get_db)):
    """Manual Case Entry (Current Money only).

    If matching synthetic transaction exists: Links to real transaction and accounts.
    If no matching transaction exists: Creates Unverified Lead without fabricating data.
    """
    bank = db.execute(select(Bank).where(Bank.bank_code == req.bank_code)).scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=400, detail=f"Bank code '{req.bank_code}' is not registered")

    # Search for matching transaction
    matched_txn = None
    if req.transaction_reference:
        matched_txn = db.execute(
            select(Transaction).where(
                Transaction.originating_bank_id == bank.id,
                Transaction.native_transaction_reference == req.transaction_reference.strip(),
            )
        ).scalar_one_or_none()

    if not matched_txn and req.account_reference:
        acc = db.execute(
            select(Account).where(
                Account.bank_id == bank.id,
                Account.bank_account_reference == req.account_reference.strip(),
            )
        ).scalar_one_or_none()
        if acc:
            matched_txn = db.execute(
                select(Transaction).where(
                    (Transaction.source_account_id == acc.id) | (Transaction.destination_account_id == acc.id)
                ).order_by(Transaction.event_timestamp.desc())
            ).scalars().first()

    is_verified = matched_txn is not None
    case_ref = f"CM-MAN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    title = f"Manual Lead: {req.suspicion_category} [{req.bank_code}]" if is_verified else f"Unverified Lead: {req.suspicion_category} [{req.bank_code}]"

    summary = (
        f"Verified lead linked to transaction {matched_txn.native_transaction_reference}. Investigator notes: {req.description}"
        if is_verified
        else f"UNVERIFIED LEAD: No matching synthetic transaction record found in database. Investigator notes: {req.description}"
    )

    case = Case(
        id=str(uuid.uuid4()),
        case_reference=case_ref,
        domain="current_money",
        title=title,
        summary=summary,
        status="OPEN",
        priority="HIGH" if is_verified else "LOW",
        risk_band="HIGH" if is_verified else "LOW",
        aggregate_risk_score=Decimal("75.00") if is_verified else Decimal("20.00"),
        scenario_run_id=matched_txn.scenario_run_id if matched_txn else None,
        is_manual_entry=True,
        manual_entry_data={
            "bank_code": req.bank_code,
            "input_tx_ref": req.transaction_reference,
            "input_account_ref": req.account_reference,
            "input_amount": str(req.amount) if req.amount else None,
            "suspicion_category": req.suspicion_category,
            "is_verified_match": is_verified,
        },
    )
    db.add(case)
    db.flush()

    # Add audit note
    db.add(
        CaseNote(
            id=str(uuid.uuid4()),
            case_id=case.id,
            note_type="INVESTIGATION_NOTE",
            content=f"Manual case initiated. Verified match: {is_verified}. Input: {req.description}",
            new_status="OPEN",
        )
    )

    if is_verified and matched_txn:
        # Link matched transaction and its accounts
        db.add(CaseTransaction(id=str(uuid.uuid4()), case_id=case.id, transaction_id=matched_txn.id, evidence_type="DIRECT"))
        db.add(CaseAccount(id=str(uuid.uuid4()), case_id=case.id, account_id=matched_txn.source_account_id, role="suspect"))
        db.add(CaseAccount(id=str(uuid.uuid4()), case_id=case.id, account_id=matched_txn.destination_account_id, role="suspect"))

    db.commit()
    return get_case(case.id, db)

