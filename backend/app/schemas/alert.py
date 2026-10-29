from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AlertRead(BaseModel):
    id: str
    domain: str
    scenario_run_id: Optional[str] = None
    account_id: Optional[str] = None
    transaction_id: Optional[str] = None
    account_ref: Optional[str] = None
    transaction_ref: Optional[str] = None
    bank_code: Optional[str] = None
    risk_score: Decimal
    risk_band: str
    signals: List[Dict[str, Any]]
    detector_version: str
    review_status: str
    created_at: datetime
    updated_at: datetime


class AlertReviewRequest(BaseModel):
    review_status: str  # REVIEWED, DISMISSED, PENDING

