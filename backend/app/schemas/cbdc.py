from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class CBDCWalletRead(BaseModel):
    id: str
    wallet_address: str
    display_name: Optional[str] = None
    wallet_type: str
    balance: Decimal
    synthetic_classification: Optional[str] = None
    is_active: bool
    created_at: datetime


class CBDCTokenLotRead(BaseModel):
    id: str
    lot_reference: str
    current_holder_wallet_id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime


class CBDCLedgerEventRead(BaseModel):
    id: str
    scenario_run_id: Optional[str] = None
    event_type: str
    from_wallet_id: Optional[str] = None
    to_wallet_id: str
    from_wallet_address: Optional[str] = None
    to_wallet_address: Optional[str] = None
    amount: Decimal
    currency: str
    event_timestamp: datetime
    parent_lot_ids: Optional[List[str]] = None
    child_lot_ids: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class CBDCProvenanceResponse(BaseModel):
    targetLot: Dict[str, Any]
    parents: List[Dict[str, Any]]
    children: List[Dict[str, Any]]

