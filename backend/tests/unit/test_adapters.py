from decimal import Decimal
import pytest
from app.adapters import (
    BankAAdapter,
    BankBAdapter,
    BankCAdapter,
    BankDAdapter,
    BankAdapterValidationError,
    get_adapter_for_bank,
)
from app.schemas.canonical import TransactionStatus, TransactionType


# ==============================================================================
# Bank A Adapter Tests
# ==============================================================================

def test_bank_a_valid_record():
    adapter = BankAAdapter()
    raw = {
        "txn_id": "TXA-998822",
        "src_account": "ACC-A-100",
        "dst_account": "ACC-A-200",
        "txn_amount": "1450.75",
        "currency_code": "USD",
        "timestamp_iso": "2026-10-28T12:00:00Z",
        "status": "COMPLETED",
        "transfer_kind": "WIRE",
    }
    canonical = adapter.normalize(raw)
    assert canonical.native_bank_code == "BNK_A"
    assert canonical.native_transaction_reference == "TXA-998822"
    assert canonical.source_account_reference == "ACC-A-100"
    assert canonical.destination_account_reference == "ACC-A-200"
    assert canonical.amount == Decimal("1450.7500")
    assert canonical.currency == "USD"
    assert canonical.status == TransactionStatus.COMPLETED
    assert canonical.normalized_type == TransactionType.TRANSFER
    assert canonical.raw_payload == raw
    assert canonical.source_adapter_version == "bank_a_adapter_v1"


def test_bank_a_rejects_negative_amount():
    adapter = BankAAdapter()
    raw = {
        "txn_id": "TXA-998822",
        "src_account": "ACC-A-100",
        "dst_account": "ACC-A-200",
        "txn_amount": "-100.00",
        "currency_code": "USD",
        "timestamp_iso": "2026-10-28T12:00:00Z",
    }
    with pytest.raises(BankAdapterValidationError) as exc:
        adapter.normalize(raw)
    assert "strictly positive" in str(exc.value)


def test_bank_a_rejects_missing_field():
    adapter = BankAAdapter()
    raw = {
        "txn_id": "TXA-998822",
        # Missing src_account
        "dst_account": "ACC-A-200",
        "txn_amount": "100.00",
        "currency_code": "USD",
        "timestamp_iso": "2026-10-28T12:00:00Z",
    }
    with pytest.raises(BankAdapterValidationError) as exc:
        adapter.normalize(raw)
    assert "Missing required field 'src_account'" in str(exc.value)


def test_bank_a_rejects_self_transfer():
    adapter = BankAAdapter()
    raw = {
        "txn_id": "TXA-998822",
        "src_account": "ACC-SAME",
        "dst_account": "ACC-SAME",
        "txn_amount": "100.00",
        "currency_code": "USD",
        "timestamp_iso": "2026-10-28T12:00:00Z",
    }
    with pytest.raises(BankAdapterValidationError) as exc:
        adapter.normalize(raw)
    assert "cannot be identical" in str(exc.value)


# ==============================================================================
# Bank B Adapter Tests
# ==============================================================================

def test_bank_b_valid_record():
    adapter = BankBAdapter()
    raw = {
        "TRANSACTION_REF": "BNKB-554433",
        "SND_ACCT_NO": "BKN-111",
        "RCV_ACCT_NO": "BKN-222",
        "TX_AMT_CENTS": 250050,  # $2,500.50
        "CCY": "USD",
        "TX_DATE": "20261028",
        "TX_TIME": "143000",
        "POST_STATUS": "SETTLED",
        "TX_CODE": "TRF",
    }
    canonical = adapter.normalize(raw)
    assert canonical.native_bank_code == "BNK_B"
    assert canonical.native_transaction_reference == "BNKB-554433"
    assert canonical.amount == Decimal("2500.5000")
    assert canonical.status == TransactionStatus.COMPLETED
    assert canonical.raw_payload == raw
    assert canonical.normalization_metadata["original_cents"] == 250050


def test_bank_b_rejects_invalid_date():
    adapter = BankBAdapter()
    raw = {
        "TRANSACTION_REF": "BNKB-554433",
        "SND_ACCT_NO": "BKN-111",
        "RCV_ACCT_NO": "BKN-222",
        "TX_AMT_CENTS": 1000,
        "CCY": "USD",
        "TX_DATE": "INVALID_DATE",
        "TX_TIME": "143000",
    }
    with pytest.raises(BankAdapterValidationError) as exc:
        adapter.normalize(raw)
    assert "Date/Time must conform" in str(exc.value)


def test_bank_b_rejects_zero_cents():
    adapter = BankBAdapter()
    raw = {
        "TRANSACTION_REF": "BNKB-554433",
        "SND_ACCT_NO": "BKN-111",
        "RCV_ACCT_NO": "BKN-222",
        "TX_AMT_CENTS": 0,
        "CCY": "USD",
        "TX_DATE": "20261028",
        "TX_TIME": "143000",
    }
    with pytest.raises(BankAdapterValidationError) as exc:
        adapter.normalize(raw)
    assert "strictly positive" in str(exc.value)


# ==============================================================================
# Bank C Adapter Tests
# ==============================================================================

def test_bank_c_valid_record():
    adapter = BankCAdapter()
    raw = {
        "endToEndId": "E2E-C-77401",
        "debtorAccount": {"iban": "CRST-DEBT-101"},
        "creditorAccount": {"iban": "CRST-CRED-202"},
        "instructedAmount": {"value": "995.25", "currency": "USD"},
        "bookingDateTime": "2026-10-28T15:45:00+00:00",
        "paymentStatus": "ACCP",
    }
    canonical = adapter.normalize(raw)
    assert canonical.native_bank_code == "BNK_C"
    assert canonical.native_transaction_reference == "E2E-C-77401"
    assert canonical.source_account_reference == "CRST-DEBT-101"
    assert canonical.destination_account_reference == "CRST-CRED-202"
    assert canonical.amount == Decimal("995.2500")
    assert canonical.status == TransactionStatus.COMPLETED
    assert canonical.raw_payload == raw


def test_bank_c_rejects_missing_account_iban():
    adapter = BankCAdapter()
    raw = {
        "endToEndId": "E2E-C-77401",
        "debtorAccount": {},  # Missing iban/account_id
        "creditorAccount": {"iban": "CRST-CRED-202"},
        "instructedAmount": {"value": "995.25", "currency": "USD"},
        "bookingDateTime": "2026-10-28T15:45:00+00:00",
    }
    with pytest.raises(BankAdapterValidationError) as exc:
        adapter.normalize(raw)
    assert "Must contain non-empty 'iban'" in str(exc.value)


# ==============================================================================
# Bank D Adapter Tests
# ==============================================================================

def test_bank_d_valid_record():
    adapter = BankDAdapter()
    raw = {
        "payment_id": "pay_d_112233",
        "sender": {"account_id": "DD-SND-901"},
        "recipient": {"account_id": "DD-REC-902"},
        "amount": "5000.00",
        "currency": "USD",
        "unix_epoch_ms": 1793197800000,
        "state": "succeeded",
        "type": "direct_transfer",
    }
    canonical = adapter.normalize(raw)
    assert canonical.native_bank_code == "BNK_D"
    assert canonical.native_transaction_reference == "pay_d_112233"
    assert canonical.source_account_reference == "DD-SND-901"
    assert canonical.destination_account_reference == "DD-REC-902"
    assert canonical.amount == Decimal("5000.0000")
    assert canonical.status == TransactionStatus.COMPLETED
    assert canonical.raw_payload == raw


def test_bank_d_rejects_invalid_epoch():
    adapter = BankDAdapter()
    raw = {
        "payment_id": "pay_d_112233",
        "sender": {"account_id": "DD-SND-901"},
        "recipient": {"account_id": "DD-REC-902"},
        "amount": "500.00",
        "currency": "USD",
        "unix_epoch_ms": -100,  # Negative epoch
        "state": "succeeded",
    }
    with pytest.raises(BankAdapterValidationError) as exc:
        adapter.normalize(raw)
    assert "positive Unix epoch" in str(exc.value)


# ==============================================================================
# Adapter Registry Test
# ==============================================================================

def test_adapter_registry_lookup():
    for code in ["BNK_A", "BNK_B", "BNK_C", "BNK_D"]:
        adapter = get_adapter_for_bank(code)
        assert adapter.bank_code == code

    with pytest.raises(ValueError):
        get_adapter_for_bank("BNK_UNKNOWN")

