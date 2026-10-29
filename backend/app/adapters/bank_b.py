from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict
from app.adapters.base import BaseBankAdapter, BankAdapterValidationError
from app.schemas.canonical import CanonicalTransaction, TransactionStatus, TransactionType


class BankBAdapter(BaseBankAdapter):
    """Adapter for Bank B (Beacon Commercial Bank).

    Native Schema (Mainframe Flat):
        TRANSACTION_REF: str
        SND_ACCT_NO: str
        RCV_ACCT_NO: str
        TX_AMT_CENTS: int (amount in integer cents)
        CCY: str
        TX_DATE: str ('YYYYMMDD')
        TX_TIME: str ('HHMMSS')
        POST_STATUS: str ('SETTLED' | 'QUEUED' | 'DECLINED')
        TX_CODE: str ('TRF' | 'PMT' | 'SET') [optional]
    """

    @property
    def bank_code(self) -> str:
        return "BNK_B"

    @property
    def adapter_version(self) -> str:
        return "bank_b_adapter_v1"

    def normalize(self, raw_record: Dict[str, Any]) -> CanonicalTransaction:
        if not isinstance(raw_record, dict):
            raise BankAdapterValidationError(
                self.adapter_version, "root", "Record must be a JSON dictionary", raw_record
            )

        required_fields = ["TRANSACTION_REF", "SND_ACCT_NO", "RCV_ACCT_NO", "TX_AMT_CENTS", "CCY", "TX_DATE", "TX_TIME"]
        for field in required_fields:
            if field not in raw_record or raw_record[field] is None:
                raise BankAdapterValidationError(
                    self.adapter_version, field, f"Missing required field '{field}'"
                )

        tx_ref = str(raw_record["TRANSACTION_REF"]).strip()
        if not tx_ref:
            raise BankAdapterValidationError(self.adapter_version, "TRANSACTION_REF", "Cannot be empty", tx_ref)

        snd_acc = str(raw_record["SND_ACCT_NO"]).strip()
        if not snd_acc:
            raise BankAdapterValidationError(self.adapter_version, "SND_ACCT_NO", "Cannot be empty", snd_acc)

        rcv_acc = str(raw_record["RCV_ACCT_NO"]).strip()
        if not rcv_acc:
            raise BankAdapterValidationError(self.adapter_version, "RCV_ACCT_NO", "Cannot be empty", rcv_acc)

        if snd_acc == rcv_acc:
            raise BankAdapterValidationError(
                self.adapter_version, "RCV_ACCT_NO", "Sender and receiver account cannot be the same", rcv_acc
            )

        # Cents conversion to Decimal
        raw_cents = raw_record["TX_AMT_CENTS"]
        try:
            cents_int = int(raw_cents)
        except (TypeError, ValueError):
            raise BankAdapterValidationError(
                self.adapter_version, "TX_AMT_CENTS", "Must be an integer value in cents", raw_cents
            )

        if cents_int <= 0:
            raise BankAdapterValidationError(
                self.adapter_version, "TX_AMT_CENTS", "Amount in cents must be strictly positive (> 0)", cents_int
            )

        amount = Decimal(cents_int) / Decimal(100)

        # Currency
        ccy = str(raw_record["CCY"]).strip().upper()
        if len(ccy) != 3 or not ccy.isalpha():
            raise BankAdapterValidationError(
                self.adapter_version, "CCY", "Currency code must be 3 letters", ccy
            )

        # Date & Time parsing (YYYYMMDD and HHMMSS, assumed UTC for standardized mainframe feeds)
        raw_date = str(raw_record["TX_DATE"]).strip()
        raw_time = str(raw_record["TX_TIME"]).strip()
        try:
            combined = f"{raw_date}{raw_time}"
            dt = datetime.strptime(combined, "%Y%m%d%H%M%S")
            dt_utc = dt.replace(tzinfo=timezone.utc)
        except Exception:
            raise BankAdapterValidationError(
                self.adapter_version,
                "TX_DATE/TX_TIME",
                "Date/Time must conform to YYYYMMDD and HHMMSS",
                f"{raw_date} {raw_time}",
            )

        # Status mapping
        raw_status = str(raw_record.get("POST_STATUS", "SETTLED")).strip().upper()
        status_map = {
            "SETTLED": TransactionStatus.COMPLETED,
            "QUEUED": TransactionStatus.PENDING,
            "DECLINED": TransactionStatus.REJECTED,
            "FAILED": TransactionStatus.FAILED,
        }
        if raw_status not in status_map:
            raise BankAdapterValidationError(
                self.adapter_version, "POST_STATUS", f"Unsupported status '{raw_status}'", raw_status
            )
        status = status_map[raw_status]

        # Normalized type mapping
        raw_code = str(raw_record.get("TX_CODE", "TRF")).strip().upper()
        if raw_code in ("PMT", "BILL"):
            norm_type = TransactionType.PAYMENT
        elif raw_code in ("SET", "CLR"):
            norm_type = TransactionType.SETTLEMENT
        else:
            norm_type = TransactionType.TRANSFER

        metadata = {
            "normalized_at": datetime.now(timezone.utc).isoformat(),
            "adapter": self.adapter_version,
            "original_cents": cents_int,
            "raw_tx_code": raw_record.get("TX_CODE"),
        }

        return CanonicalTransaction(
            native_bank_code=self.bank_code,
            native_transaction_reference=tx_ref,
            source_account_reference=snd_acc,
            destination_account_reference=rcv_acc,
            amount=amount,
            currency=ccy,
            event_timestamp=dt_utc,
            normalized_type=norm_type,
            status=status,
            source_adapter_version=self.adapter_version,
            raw_payload=raw_record,
            normalization_metadata=metadata,
        )

