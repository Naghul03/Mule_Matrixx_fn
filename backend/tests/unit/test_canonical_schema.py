from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.canonical import (
    CanonicalTransaction,
    TransactionType,
    TransactionStatus,
)


def test_valid_canonical_transaction():
    txn = CanonicalTransaction(
        native_bank_code="BNK_A",
        native_transaction_reference="REF-001",
        source_account_reference="ACC-101",
        destination_account_reference="ACC-202",
        amount=Decimal("1250.5000"),
        currency="USD",
        event_timestamp=datetime(2026, 10, 28, 14, 0, 0, tzinfo=timezone.utc),
        normalized_type=TransactionType.TRANSFER,
        status=TransactionStatus.COMPLETED,
        source_adapter_version="bank_a_adapter_v1",
        raw_payload={"sample": "data"},
        normalization_metadata={"source": "unit_test"},
    )
    assert txn.native_bank_code == "BNK_A"
    assert txn.amount == Decimal("1250.5000")
    assert isinstance(txn.amount, Decimal)
    assert txn.currency == "USD"
    assert txn.event_timestamp.tzinfo is not None


def test_reject_zero_or_negative_amount():
    with pytest.raises(ValidationError):
        CanonicalTransaction(
            native_bank_code="BNK_A",
            native_transaction_reference="REF-001",
            source_account_reference="ACC-101",
            destination_account_reference="ACC-202",
            amount=Decimal("0.0000"),
            currency="USD",
            event_timestamp=datetime.now(timezone.utc),
            normalized_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            source_adapter_version="bank_a_adapter_v1",
            raw_payload={},
        )

    with pytest.raises(ValidationError):
        CanonicalTransaction(
            native_bank_code="BNK_A",
            native_transaction_reference="REF-001",
            source_account_reference="ACC-101",
            destination_account_reference="ACC-202",
            amount=Decimal("-50.00"),
            currency="USD",
            event_timestamp=datetime.now(timezone.utc),
            normalized_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            source_adapter_version="bank_a_adapter_v1",
            raw_payload={},
        )


def test_reject_self_transfer():
    with pytest.raises(ValidationError) as exc:
        CanonicalTransaction(
            native_bank_code="BNK_A",
            native_transaction_reference="REF-001",
            source_account_reference="ACC-SAME",
            destination_account_reference="ACC-SAME",
            amount=Decimal("100.00"),
            currency="USD",
            event_timestamp=datetime.now(timezone.utc),
            normalized_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            source_adapter_version="bank_a_adapter_v1",
            raw_payload={},
        )
    assert "Self-transfer rejected" in str(exc.value)


def test_reject_naive_timestamp():
    with pytest.raises(ValidationError) as exc:
        CanonicalTransaction(
            native_bank_code="BNK_A",
            native_transaction_reference="REF-001",
            source_account_reference="ACC-101",
            destination_account_reference="ACC-202",
            amount=Decimal("100.00"),
            currency="USD",
            event_timestamp=datetime(2026, 10, 28, 14, 0, 0),  # Naive without tzinfo
            normalized_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            source_adapter_version="bank_a_adapter_v1",
            raw_payload={},
        )
    assert "timezone-aware" in str(exc.value)


def test_reject_invalid_currency():
    with pytest.raises(ValidationError):
        CanonicalTransaction(
            native_bank_code="BNK_A",
            native_transaction_reference="REF-001",
            source_account_reference="ACC-101",
            destination_account_reference="ACC-202",
            amount=Decimal("100.00"),
            currency="US",  # Invalid: 2 letters
            event_timestamp=datetime.now(timezone.utc),
            normalized_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            source_adapter_version="bank_a_adapter_v1",
            raw_payload={},
        )

