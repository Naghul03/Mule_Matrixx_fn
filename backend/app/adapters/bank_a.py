from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict
from app.adapters.base import BaseBankAdapter, BankAdapterValidationError
from app.schemas.canonical import CanonicalTransaction, TransactionStatus, TransactionType


class BankAAdapter(BaseBankAdapter):
    """Adapter for Bank A (Apex National Bank).

    Native Schema:
        txn_id: str
        src_account: str
        dst_account: str
        txn_amount: str | Decimal
        currency_code: str
        timestamp_iso: str (ISO-8601 with tz)
        status: str ('COMPLETED' | 'PENDING' | 'FAILED')
        transfer_kind: str ('WIRE' | 'ACH' | 'INTERNAL') [optional]
    """

    @property
    def bank_code(self) -> str:
        return "BNK_A"

    @property
    def adapter_version(self) -> str:
        return "bank_a_adapter_v1"

    def normalize(self, raw_record: Dict[str, Any]) -> CanonicalTransaction:
        if not isinstance(raw_record, dict):
            raise BankAdapterValidationError(
                self.adapter_version, "root", "Record must be a JSON dictionary", raw_record
            )

        # Required fields check
        required_fields = ["txn_id", "src_account", "dst_account", "txn_amount", "currency_code", "timestamp_iso"]
        for field in required_fields:
            if field not in raw_record or raw_record[field] is None:
                raise BankAdapterValidationError(
                    self.adapter_version, field, f"Missing required field '{field}'"
                )

        txn_id = str(raw_record["txn_id"]).strip()
        if not txn_id:
            raise BankAdapterValidationError(self.adapter_version, "txn_id", "Cannot be empty", raw_record["txn_id"])

        src_acc = str(raw_record["src_account"]).strip()
        if not src_acc:
            raise BankAdapterValidationError(self.adapter_version, "src_account", "Cannot be empty", raw_record["src_account"])

        dst_acc = str(raw_record["dst_account"]).strip()
        if not dst_acc:
            raise BankAdapterValidationError(self.adapter_version, "dst_account", "Cannot be empty", raw_record["dst_account"])

        if src_acc == dst_acc:
            raise BankAdapterValidationError(
                self.adapter_version, "dst_account", "Source and destination accounts cannot be identical", dst_acc
            )

        # Amount validation
        raw_amt = raw_record["txn_amount"]
        try:
            amt = Decimal(str(raw_amt).strip())
        except (InvalidOperation, TypeError, ValueError):
            raise BankAdapterValidationError(
                self.adapter_version, "txn_amount", "Amount must be a valid numeric value", raw_amt
            )

        if amt <= Decimal("0"):
            raise BankAdapterValidationError(
                self.adapter_version, "txn_amount", "Amount must be strictly positive", raw_amt
            )

        # Currency
        ccy = str(raw_record["currency_code"]).strip().upper()
        if len(ccy) != 3 or not ccy.isalpha():
            raise BankAdapterValidationError(
                self.adapter_version, "currency_code", "Currency code must be 3 letters", ccy
            )

        # Timestamp
        raw_ts = str(raw_record["timestamp_iso"]).strip()
        try:
            # Handle ISO format including trailing 'Z'
            ts_str = raw_ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                raise ValueError("Naive timestamp")
            dt_utc = dt.astimezone(timezone.utc)
        except Exception:
            raise BankAdapterValidationError(
                self.adapter_version, "timestamp_iso", "Must be a valid ISO-8601 timezone-aware timestamp", raw_ts
            )

        # Status mapping
        raw_status = str(raw_record.get("status", "COMPLETED")).strip().upper()
        status_map = {
            "COMPLETED": TransactionStatus.COMPLETED,
            "SUCCESS": TransactionStatus.COMPLETED,
            "SETTLED": TransactionStatus.COMPLETED,
            "PENDING": TransactionStatus.PENDING,
            "FAILED": TransactionStatus.FAILED,
            "REJECTED": TransactionStatus.REJECTED,
        }
        if raw_status not in status_map:
            raise BankAdapterValidationError(
                self.adapter_version, "status", f"Unsupported status '{raw_status}'", raw_status
            )
        status = status_map[raw_status]

        # Normalized type mapping
        raw_kind = str(raw_record.get("transfer_kind", "WIRE")).strip().upper()
        if raw_kind in ("ACH", "BILL_PAY"):
            norm_type = TransactionType.PAYMENT
        else:
            norm_type = TransactionType.TRANSFER

        metadata = {
            "normalized_at": datetime.now(timezone.utc).isoformat(),
            "adapter": self.adapter_version,
            "raw_transfer_kind": raw_record.get("transfer_kind"),
        }

        return CanonicalTransaction(
            native_bank_code=self.bank_code,
            native_transaction_reference=txn_id,
            source_account_reference=src_acc,
            destination_account_reference=dst_acc,
            amount=amt,
            currency=ccy,
            event_timestamp=dt_utc,
            normalized_type=norm_type,
            status=status,
            source_adapter_version=self.adapter_version,
            raw_payload=raw_record,
            normalization_metadata=metadata,
        )

