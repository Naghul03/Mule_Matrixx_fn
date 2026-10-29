from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BankBase(BaseModel):
    bank_code: str = Field(..., min_length=2, max_length=16)
    display_name: str = Field(..., min_length=1, max_length=128)
    adapter_identifier: str = Field(..., min_length=1, max_length=64)
    is_enabled: bool = True


class BankCreate(BankBase):
    pass


class BankRead(BankBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime

