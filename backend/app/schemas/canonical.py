from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    SETTLEMENT = "SETTLEMENT"


class TransactionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class CanonicalTransaction(BaseModel):
    """Canonical Transaction Contract.

    All simulated bank transactions must be normalized to this schema.
    Amounts must use exact Decimal representations (strictly positive).
    Timestamps must be timezone-aware UTC datetime instances.
    Self-transfers are explicitly forbidden.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    native_bank_code: str = Field(..., min_length=2, max_length=16, description="Standard bank code")
    native_transaction_reference: str = Field(..., min_length=1, max_length=128, description="Bank-native reference")
    source_account_reference: str = Field(..., min_length=1, max_length=64, description="Debtor account reference")
    destination_account_reference: str = Field(..., min_length=1, max_length=64, description="Creditor account reference")
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Strictly positive financial amount")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    event_timestamp: datetime = Field(..., description="UTC event timestamp")
    normalized_type: TransactionType = Field(default=TransactionType.TRANSFER, description="Normalized transaction type")
    status: TransactionStatus = Field(default=TransactionStatus.COMPLETED, description="Normalized execution status")
    source_adapter_version: str = Field(..., min_length=1, max_length=64, description="Adapter name and version")
    raw_payload: Dict[str, Any] = Field(..., description="Faithful preservation of the native payload")
    normalization_metadata: Dict[str, Any] = Field(default_factory=dict, description="Adapter normalization metadata")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if len(v_upper) != 3 or not v_upper.isalpha():
            raise ValueError(f"Invalid currency code '{v}'. Must be 3 alphabetic characters.")
        return v_upper

    @field_validator("event_timestamp")
    @classmethod
    def validate_event_timestamp(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            # Reject naive timestamps - callers/adapters must be explicit about timezone
            raise ValueError("Event timestamp must be timezone-aware.")
        return v.astimezone(timezone.utc)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError(f"Transaction amount must be strictly positive. Received: {v}")
        # Normalize to 4 decimal places
        return v.quantize(Decimal("0.0001"))

    @model_validator(mode="after")
    def validate_no_self_transfer(self) -> "CanonicalTransaction":
        if self.source_account_reference.strip() == self.destination_account_reference.strip():
            raise ValueError(
                f"Self-transfer rejected: source account '{self.source_account_reference}' "
                f"cannot be the same as destination account."
            )
        return self

