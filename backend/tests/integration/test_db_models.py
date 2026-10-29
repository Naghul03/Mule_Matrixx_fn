from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from app.db.models.bank import Bank
from app.db.models.account import Account
from app.db.models.scenario_run import ScenarioRun
from app.db.models.transaction import Transaction
from app.db.models.ground_truth import GroundTruthLabel


def test_bank_creation_and_uniqueness(db_session):
    bank = Bank(
        bank_code=f"TEST_{uuid.uuid4().hex[:6]}",
        display_name="Test Bank",
        adapter_identifier="test_adapter_v1",
        is_enabled=True,
    )
    db_session.add(bank)
    db_session.flush()
    assert bank.id is not None

    # Test unique constraint on bank_code
    duplicate = Bank(
        bank_code=bank.bank_code,
        display_name="Duplicate Bank",
        adapter_identifier="test_adapter_v1",
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError) as exc:
        db_session.flush()
    assert "Duplicate entry" in str(exc.value)


def test_account_creation_and_uniqueness_within_bank(db_session):
    bank = db_session.execute(select(Bank).where(Bank.bank_code == "BNK_A")).scalar_one()

    acc1 = Account(
        bank_id=bank.id,
        bank_account_reference=f"ACC_{uuid.uuid4().hex[:8]}",
        display_alias="Primary Account",
    )
    db_session.add(acc1)
    db_session.flush()

    # Same reference within same bank should fail
    acc_dup = Account(
        bank_id=bank.id,
        bank_account_reference=acc1.bank_account_reference,
    )
    db_session.add(acc_dup)
    with pytest.raises(IntegrityError) as exc:
        db_session.flush()
    assert "Duplicate entry" in str(exc.value)


def test_monetary_precision_preserved(db_session):
    bank = db_session.execute(select(Bank).where(Bank.bank_code == "BNK_A")).scalar_one()

    acc_src = Account(bank_id=bank.id, bank_account_reference=f"SRC_{uuid.uuid4().hex[:8]}")
    acc_dst = Account(bank_id=bank.id, bank_account_reference=f"DST_{uuid.uuid4().hex[:8]}")
    db_session.add_all([acc_src, acc_dst])
    db_session.flush()

    exact_amount = Decimal("1234567.8912")
    txn = Transaction(
        originating_bank_id=bank.id,
        source_account_id=acc_src.id,
        destination_account_id=acc_dst.id,
        amount=exact_amount,
        currency="USD",
        event_timestamp=datetime.now(timezone.utc),
        native_transaction_reference=f"REF_{uuid.uuid4().hex[:8]}",
        normalized_type="TRANSFER",
        status="COMPLETED",
        source_adapter_version="bank_a_adapter_v1",
        raw_payload={"test": "precision"},
        normalization_metadata={},
    )
    db_session.add(txn)
    db_session.flush()

    # Query back and verify exact Decimal representation
    fetched = db_session.execute(select(Transaction).where(Transaction.id == txn.id)).scalar_one()
    assert isinstance(fetched.amount, Decimal)
    assert fetched.amount == exact_amount


def test_multiple_transactions_between_same_accounts_allowed(db_session):
    bank = db_session.execute(select(Bank).where(Bank.bank_code == "BNK_A")).scalar_one()

    acc_src = Account(bank_id=bank.id, bank_account_reference=f"SRC_{uuid.uuid4().hex[:8]}")
    acc_dst = Account(bank_id=bank.id, bank_account_reference=f"DST_{uuid.uuid4().hex[:8]}")
    db_session.add_all([acc_src, acc_dst])
    db_session.flush()

    # Insert two separate transactions between same accounts
    t1 = Transaction(
        originating_bank_id=bank.id,
        source_account_id=acc_src.id,
        destination_account_id=acc_dst.id,
        amount=Decimal("100.0000"),
        currency="USD",
        event_timestamp=datetime.now(timezone.utc),
        native_transaction_reference=f"TX_{uuid.uuid4().hex[:8]}",
        normalized_type="TRANSFER",
        status="COMPLETED",
        source_adapter_version="bank_a_adapter_v1",
        raw_payload={},
        normalization_metadata={},
    )
    t2 = Transaction(
        originating_bank_id=bank.id,
        source_account_id=acc_src.id,
        destination_account_id=acc_dst.id,
        amount=Decimal("200.0000"),
        currency="USD",
        event_timestamp=datetime.now(timezone.utc),
        native_transaction_reference=f"TX_{uuid.uuid4().hex[:8]}",
        normalized_type="TRANSFER",
        status="COMPLETED",
        source_adapter_version="bank_a_adapter_v1",
        raw_payload={},
        normalization_metadata={},
    )
    db_session.add_all([t1, t2])
    db_session.flush()
    assert t1.id != t2.id


def test_reject_self_transfer_check_constraint(db_session):
    bank = db_session.execute(select(Bank).where(Bank.bank_code == "BNK_A")).scalar_one()
    acc = Account(bank_id=bank.id, bank_account_reference=f"ACC_{uuid.uuid4().hex[:8]}")
    db_session.add(acc)
    db_session.flush()

    invalid_txn = Transaction(
        originating_bank_id=bank.id,
        source_account_id=acc.id,
        destination_account_id=acc.id,  # Self transfer violates check constraint
        amount=Decimal("50.0000"),
        currency="USD",
        event_timestamp=datetime.now(timezone.utc),
        native_transaction_reference=f"TX_{uuid.uuid4().hex[:8]}",
        normalized_type="TRANSFER",
        status="COMPLETED",
        source_adapter_version="bank_a_adapter_v1",
        raw_payload={},
        normalization_metadata={},
    )
    db_session.add(invalid_txn)
    with pytest.raises((IntegrityError, OperationalError)) as exc:
        db_session.flush()
    assert "ck_transactions_no_self_transfer" in str(exc.value)


def test_scenario_run_and_ground_truth_isolation(db_session):
    run = ScenarioRun(
        domain="current_money",
        scenario_identifier="structuring_fan_out_v1",
        scenario_version="1.0.0",
        generator_version="1.0.0",
        seed=1337,
        configuration_json={"fan_out_degree": 5, "base_amount": 9500},
        status="COMPLETED",
    )
    db_session.add(run)
    db_session.flush()

    # Ground truth is recorded in separate table
    gt = GroundTruthLabel(
        scenario_run_id=run.id,
        role_label="mule_recruiter",
        expected_relationship="fan_out_source",
        rationale="Simulated account distributing structured funds",
    )
    db_session.add(gt)
    db_session.flush()

    assert gt.id is not None
    assert gt.role_label == "mule_recruiter"
