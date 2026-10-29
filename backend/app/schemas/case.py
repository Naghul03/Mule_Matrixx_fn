from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaseRead(BaseModel):
    id: str
    case_reference: str
    domain: str
    title: str
    summary: Optional[str] = None
    status: str
    priority: str
    risk_band: Optional[str] = None
    aggregate_risk_score: Optional[Decimal] = None
    scenario_run_id: Optional[str] = None
    is_manual_entry: bool = False
    manual_entry_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    alert_count: int = 0
    account_count: int = 0
    transaction_count: int = 0


class CaseDetail(CaseRead):
    alerts: List[Dict[str, Any]] = []
    accounts: List[Dict[str, Any]] = []
    transactions: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []


class CaseStatusUpdateRequest(BaseModel):
    status: str  # OPEN, UNDER_INVESTIGATION, ESCALATED, CLOSED
    note: str = Field(..., min_length=2, description="Investigator rationale for status transition")


class ManualCaseCreateRequest(BaseModel):
    bank_code: str = Field(..., description="BNK_A, BNK_B, BNK_C, or BNK_D")
    transaction_reference: Optional[str] = None
    account_reference: Optional[str] = None
    amount: Optional[Decimal] = None
    event_date: Optional[str] = None
    suspicion_category: str = Field(default="SUSPICIOUS_PASS_THROUGH")
    description: str = Field(..., min_length=5, description="Investigator notes describing the concern")

