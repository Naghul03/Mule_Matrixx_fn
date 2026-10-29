import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.adapters import get_adapter_for_bank, BankAdapterValidationError
from app.db.models.bank import Bank
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.schemas.canonical import CanonicalTransaction

logger = logging.getLogger(__name__)


class TransactionIngestionService:
    """Service responsible for validating, normalizing, and recording financial transactions."""

    def __init__(self, db: Session):
        self.db = db

    def normalize_native_transaction(
        self, bank_code: str, raw_payload: Dict[str, Any]
    ) -> CanonicalTransaction:
        """Normalize a bank payload using the respective registered adapter."""
        adapter = get_adapter_for_bank(bank_code)
        return adapter.normalize(raw_payload)

    def ingest_transaction(
        self,
        bank_code: str,
        raw_payload: Dict[str, Any],
        scenario_run_id: Optional[str] = None,
    ) -> Transaction:
        """Normalize and persist a transaction into the canonical database schema.

        Enforces bank resolution, account resolution/creation, and idempotency.
        """
        canonical = self.normalize_native_transaction(bank_code, raw_payload)

        # 1. Resolve Bank
        bank = self.db.execute(
            select(Bank).where(Bank.bank_code == canonical.native_bank_code)
        ).scalar_one_or_none()

        if not bank:
            # Register or fail - in Module 1 simulation, bank must be registered
            raise ValueError(f"Originating bank '{canonical.native_bank_code}' is not registered.")

        # 2. Check Idempotency (Originating bank + native transaction reference)
        if canonical.native_transaction_reference:
            existing = self.db.execute(
                select(Transaction).where(
                    Transaction.originating_bank_id == bank.id,
                    Transaction.native_transaction_reference == canonical.native_transaction_reference,
                )
            ).scalar_one_or_none()

            if existing:
                logger.info(
                    "Duplicate transaction detected for bank %s with ref %s. Returning existing.",
                    bank.bank_code,
                    canonical.native_transaction_reference,
                )
                return existing

        # 3. Resolve or create source account
        source_acc = self.db.execute(
            select(Account).where(
                Account.bank_account_reference == canonical.source_account_reference
            )
        ).scalars().first()

        if not source_acc:
            source_acc = Account(
                bank_id=bank.id,
                bank_account_reference=canonical.source_account_reference,
                display_alias=f"Account {canonical.source_account_reference}",
            )
            self.db.add(source_acc)
            self.db.flush()

        # 4. Resolve or create destination account
        dest_acc = self.db.execute(
            select(Account).where(
                Account.bank_account_reference == canonical.destination_account_reference
            )
        ).scalars().first()

        if not dest_acc:
            dest_acc = Account(
                bank_id=bank.id,
                bank_account_reference=canonical.destination_account_reference,
                display_alias=f"Account {canonical.destination_account_reference}",
            )
            self.db.add(dest_acc)
            self.db.flush()

        # 5. Create Transaction entity
        txn = Transaction(
            scenario_run_id=scenario_run_id,
            originating_bank_id=bank.id,
            source_account_id=source_acc.id,
            destination_account_id=dest_acc.id,
            amount=canonical.amount,
            currency=canonical.currency,
            event_timestamp=canonical.event_timestamp,
            native_transaction_reference=canonical.native_transaction_reference,
            normalized_type=canonical.normalized_type.value,
            status=canonical.status.value,
            source_adapter_version=canonical.source_adapter_version,
            raw_payload=canonical.raw_payload,
            normalization_metadata=canonical.normalization_metadata,
        )

        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn

