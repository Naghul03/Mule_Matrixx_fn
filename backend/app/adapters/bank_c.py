from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict
from app.adapters.base import BaseBankAdapter, BankAdapterValidationError
from app.schemas.canonical import CanonicalTransaction, TransactionStatus, TransactionType


class BankCAdapter(BaseBankAdapter):
    """Adapter for Bank C (Crestline Trust).

    Native Schema (ISO 20022 / SEPA Style):
        endToEndId: str
        debtorAccount: {"iban": str} or {"account_id": str}
        creditorAccount: {"iban": str} or {"account_id": str}
        instructedAmount: {"value": str | Decimal, "currency": str}
        bookingDateTime: str (ISO-8601 with tz offset)
        paymentStatus: str ('ACCP' | 'PDNG' | 'RJCT' | 'CANC')
    """

    @property
    def bank_code(self) -> str:
        return "BNK_C"

    @property
    def adapter_version(self) -> str:
        return "bank_c_adapter_v1"

    def normalize(self, raw_record: Dict[str, Any]) -> CanonicalTransaction:
        if not isinstance(raw_record, dict):
            raise BankAdapterValidationError(
                self.adapter_version, "root", "Record must be a JSON dictionary", raw_record
            )

        required_fields = ["endToEndId", "debtorAccount", "creditorAccount", "instructedAmount", "bookingDateTime"]
        for field in required_fields:
            if field not in raw_record or raw_record[field] is None:
                raise BankAdapterValidationError(
                    self.adapter_version, field, f"Missing required field '{field}'"
                )

        e2e_id = str(raw_record["endToEndId"]).strip()
        if not e2e_id:
            raise BankAdapterValidationError(self.adapter_version, "endToEndId", "Cannot be empty", e2e_id)

        # Debtor account
        debtor_obj = raw_record["debtorAccount"]
        if not isinstance(debtor_obj, dict):
            raise BankAdapterValidationError(
                self.adapter_version, "debtorAccount", "Must be a dictionary object", debtor_obj
            )
        deb_acc = str(debtor_obj.get("iban") or debtor_obj.get("account_id") or "").strip()
        if not deb_acc:
            raise BankAdapterValidationError(
                self.adapter_version, "debtorAccount", "Must contain non-empty 'iban' or 'account_id'", debtor_obj
            )

        # Creditor account
        creditor_obj = raw_record["creditorAccount"]
        if not isinstance(creditor_obj, dict):
            raise BankAdapterValidationError(
                self.adapter_version, "creditorAccount", "Must be a dictionary object", creditor_obj
            )
        cred_acc = str(creditor_obj.get("iban") or creditor_obj.get("account_id") or "").strip()
        if not cred_acc:
            raise BankAdapterValidationError(
                self.adapter_version, "creditorAccount", "Must contain non-empty 'iban' or 'account_id'", creditor_obj
            )

        if deb_acc == cred_acc:
            raise BankAdapterValidationError(
                self.adapter_version, "creditorAccount", "Debtor and creditor accounts cannot be identical", cred_acc
            )

        # Instructed Amount
        inst_amt = raw_record["instructedAmount"]
        if not isinstance(inst_amt, dict) or "value" not in inst_amt or "currency" not in inst_amt:
            raise BankAdapterValidationError(
                self.adapter_version, "instructedAmount", "Must contain 'value' and 'currency'", inst_amt
            )

        try:
            amt = Decimal(str(inst_amt["value"]).strip())
        except (InvalidOperation, TypeError, ValueError):
            raise BankAdapterValidationError(
                self.adapter_version, "instructedAmount.value", "Invalid decimal amount", inst_amt.get("value")
            )

        if amt <= Decimal("0"):
            raise BankAdapterValidationError(
                self.adapter_version, "instructedAmount.value", "Amount must be strictly positive", amt
            )

        ccy = str(inst_amt["currency"]).strip().upper()
        if len(ccy) != 3 or not ccy.isalpha():
            raise BankAdapterValidationError(
                self.adapter_version, "instructedAmount.currency", "Currency must be a 3-letter code", ccy
            )

        # Booking date time
        raw_dt = str(raw_record["bookingDateTime"]).strip()
        try:
            dt_str = raw_dt.replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                raise ValueError("Naive timestamp")
            dt_utc = dt.astimezone(timezone.utc)
        except Exception:
            raise BankAdapterValidationError(
                self.adapter_version, "bookingDateTime", "Must be an ISO-8601 timezone-aware string", raw_dt
            )

        # Status mapping
        raw_status = str(raw_record.get("paymentStatus", "ACCP")).strip().upper()
        status_map = {
            "ACCP": TransactionStatus.COMPLETED,
            "PDNG": TransactionStatus.PENDING,
            "RJCT": TransactionStatus.REJECTED,
            "CANC": TransactionStatus.FAILED,
        }
        if raw_status not in status_map:
            raise BankAdapterValidationError(
                self.adapter_version, "paymentStatus", f"Unsupported ISO 20022 status '{raw_status}'", raw_status
            )
        status = status_map[raw_status]

        metadata = {
            "normalized_at": datetime.now(timezone.utc).isoformat(),
            "adapter": self.adapter_version,
            "iso20022_status": raw_status,
        }

        return CanonicalTransaction(
            native_bank_code=self.bank_code,
            native_transaction_reference=e2e_id,
            source_account_reference=deb_acc,
            destination_account_reference=cred_acc,
            amount=amt,
            currency=ccy,
            event_timestamp=dt_utc,
            normalized_type=TransactionType.TRANSFER,
            status=status,
            source_adapter_version=self.adapter_version,
            raw_payload=raw_record,
            normalization_metadata=metadata,
        )

