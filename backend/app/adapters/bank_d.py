from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict
from app.adapters.base import BaseBankAdapter, BankAdapterValidationError
from app.schemas.canonical import CanonicalTransaction, TransactionStatus, TransactionType


class BankDAdapter(BaseBankAdapter):
    """Adapter for Bank D (Delta Direct - Modern Fintech).

    Native Schema (Fintech API):
        payment_id: str
        sender: {"account_id": str}
        recipient: {"account_id": str}
        amount: str | Decimal
        currency: str
        unix_epoch_ms: int
        state: str ('succeeded' | 'processing' | 'canceled' | 'declined')
        type: str ('direct_transfer' | 'merchant_payment') [optional]
    """

    @property
    def bank_code(self) -> str:
        return "BNK_D"

    @property
    def adapter_version(self) -> str:
        return "bank_d_adapter_v1"

    def normalize(self, raw_record: Dict[str, Any]) -> CanonicalTransaction:
        if not isinstance(raw_record, dict):
            raise BankAdapterValidationError(
                self.adapter_version, "root", "Record must be a JSON dictionary", raw_record
            )

        required_fields = ["payment_id", "sender", "recipient", "amount", "currency", "unix_epoch_ms"]
        for field in required_fields:
            if field not in raw_record or raw_record[field] is None:
                raise BankAdapterValidationError(
                    self.adapter_version, field, f"Missing required field '{field}'"
                )

        payment_id = str(raw_record["payment_id"]).strip()
        if not payment_id:
            raise BankAdapterValidationError(self.adapter_version, "payment_id", "Cannot be empty", payment_id)

        # Sender
        sender_obj = raw_record["sender"]
        if not isinstance(sender_obj, dict):
            raise BankAdapterValidationError(self.adapter_version, "sender", "Must be a dictionary object", sender_obj)
        sender_acc = str(sender_obj.get("account_id") or "").strip()
        if not sender_acc:
            raise BankAdapterValidationError(self.adapter_version, "sender.account_id", "Cannot be empty", sender_obj)

        # Recipient
        recipient_obj = raw_record["recipient"]
        if not isinstance(recipient_obj, dict):
            raise BankAdapterValidationError(self.adapter_version, "recipient", "Must be a dictionary object", recipient_obj)
        recipient_acc = str(recipient_obj.get("account_id") or "").strip()
        if not recipient_acc:
            raise BankAdapterValidationError(self.adapter_version, "recipient.account_id", "Cannot be empty", recipient_obj)

        if sender_acc == recipient_acc:
            raise BankAdapterValidationError(
                self.adapter_version, "recipient", "Sender and recipient accounts cannot be identical", recipient_acc
            )

        # Amount
        raw_amt = raw_record["amount"]
        try:
            amt = Decimal(str(raw_amt).strip())
        except (InvalidOperation, TypeError, ValueError):
            raise BankAdapterValidationError(
                self.adapter_version, "amount", "Must be a valid decimal amount", raw_amt
            )

        if amt <= Decimal("0"):
            raise BankAdapterValidationError(
                self.adapter_version, "amount", "Amount must be strictly positive", amt
            )

        # Currency
        ccy = str(raw_record["currency"]).strip().upper()
        if len(ccy) != 3 or not ccy.isalpha():
            raise BankAdapterValidationError(
                self.adapter_version, "currency", "Must be a 3-letter currency code", ccy
            )

        # Timestamp in Unix milliseconds
        raw_ms = raw_record["unix_epoch_ms"]
        try:
            ms_int = int(raw_ms)
            if ms_int <= 0:
                raise ValueError("Must be positive")
            dt_utc = datetime.fromtimestamp(ms_int / 1000.0, tz=timezone.utc)
        except Exception:
            raise BankAdapterValidationError(
                self.adapter_version, "unix_epoch_ms", "Must be a valid positive Unix epoch millisecond timestamp", raw_ms
            )

        # State mapping
        raw_state = str(raw_record.get("state", "succeeded")).strip().lower()
        state_map = {
            "succeeded": TransactionStatus.COMPLETED,
            "processing": TransactionStatus.PENDING,
            "declined": TransactionStatus.REJECTED,
            "canceled": TransactionStatus.FAILED,
            "failed": TransactionStatus.FAILED,
        }
        if raw_state not in state_map:
            raise BankAdapterValidationError(
                self.adapter_version, "state", f"Unsupported state '{raw_state}'", raw_state
            )
        status = state_map[raw_state]

        # Normalized type mapping
        raw_type = str(raw_record.get("type", "direct_transfer")).strip().lower()
        if raw_type in ("merchant_payment", "bill_pay"):
            norm_type = TransactionType.PAYMENT
        else:
            norm_type = TransactionType.TRANSFER

        metadata = {
            "normalized_at": datetime.now(timezone.utc).isoformat(),
            "adapter": self.adapter_version,
            "raw_state": raw_state,
        }

        return CanonicalTransaction(
            native_bank_code=self.bank_code,
            native_transaction_reference=payment_id,
            source_account_reference=sender_acc,
            destination_account_reference=recipient_acc,
            amount=amt,
            currency=ccy,
            event_timestamp=dt_utc,
            normalized_type=norm_type,
            status=status,
            source_adapter_version=self.adapter_version,
            raw_payload=raw_record,
            normalization_metadata=metadata,
        )

