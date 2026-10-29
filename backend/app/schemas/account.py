from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AccountBase(BaseModel):
    bank_id: str = Field(...)
    bank_account_reference: str = Field(..., min_length=1, max_length=64)
    display_alias: Optional[str] = Field(None, max_length=128)


class AccountCreate(AccountBase):
    synthetic_classification: Optional[str] = None


class AccountRead(AccountBase):
    """Detector and investigation-facing account schema.
    Ground-truth and synthetic classifications are strictly excluded.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class AccountInternalSimulation(AccountRead):
    """Internal simulation-only schema including synthetic classification for scenario generator."""
    synthetic_classification: Optional[str] = None

