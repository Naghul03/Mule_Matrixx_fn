"""Initial foundation schema

Revision ID: 0001_initial_foundation
Revises:
Create Date: 2026-10-28 16:00:00.000000 UTC

"""
from typing import Sequence, Union
from datetime import datetime, timezone
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Banks Table
    op.create_table(
        "banks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bank_code", sa.String(16), nullable=False, unique=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("adapter_identifier", sa.String(64), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_banks_bank_code", "banks", ["bank_code"])

    # 2. Accounts Table
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bank_id", sa.String(36), sa.ForeignKey("banks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("bank_account_reference", sa.String(64), nullable=False),
        sa.Column("display_alias", sa.String(128), nullable=True),
        sa.Column("synthetic_classification", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("bank_id", "bank_account_reference", name="uq_accounts_bank_ref"),
    )
    op.create_index("ix_accounts_bank_id", "accounts", ["bank_id"])

    # 3. Scenario Runs Table
    op.create_table(
        "scenario_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain", sa.String(32), nullable=False, server_default="current_money"),
        sa.Column("scenario_identifier", sa.String(64), nullable=False),
        sa.Column("scenario_version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("generator_version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("configuration_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scenario_runs_domain", "scenario_runs", ["domain"])
    op.create_index("ix_scenario_runs_created_at", "scenario_runs", ["created_at"])

    # 4. Transactions Table
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("originating_bank_id", sa.String(36), sa.ForeignKey("banks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("destination_account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("native_transaction_reference", sa.String(128), nullable=True),
        sa.Column("normalized_type", sa.String(32), nullable=False, server_default="TRANSFER"),
        sa.Column("status", sa.String(24), nullable=False, server_default="COMPLETED"),
        sa.Column("source_adapter_version", sa.String(64), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalization_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source_account_id <> destination_account_id", name="ck_transactions_no_self_transfer"),
        sa.UniqueConstraint("originating_bank_id", "native_transaction_reference", name="uq_transactions_bank_native_ref"),
    )
    op.create_index("ix_transactions_scenario_run", "transactions", ["scenario_run_id"])
    op.create_index("ix_transactions_origin_bank", "transactions", ["originating_bank_id"])
    op.create_index("ix_transactions_source_acc", "transactions", ["source_account_id"])
    op.create_index("ix_transactions_dest_acc", "transactions", ["destination_account_id"])
    op.create_index("ix_transactions_event_time", "transactions", ["event_timestamp"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])

    # 5. Ground Truth Labels Table (Strictly isolated evaluation store)
    op.create_table(
        "ground_truth_labels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("transaction_id", sa.String(36), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("role_label", sa.String(64), nullable=False),
        sa.Column("expected_relationship", sa.String(64), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gt_scenario_run", "ground_truth_labels", ["scenario_run_id"])
    op.create_index("ix_gt_account_id", "ground_truth_labels", ["account_id"])
    op.create_index("ix_gt_transaction_id", "ground_truth_labels", ["transaction_id"])

    # Seed the 4 Simulated Banks
    now = datetime.now(timezone.utc)
    banks_table = sa.table(
        "banks",
        sa.column("id", sa.String),
        sa.column("bank_code", sa.String),
        sa.column("display_name", sa.String),
        sa.column("adapter_identifier", sa.String),
        sa.column("is_enabled", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    op.bulk_insert(
        banks_table,
        [
            {
                "id": str(uuid.uuid4()),
                "bank_code": "BNK_A",
                "display_name": "Apex National Bank",
                "adapter_identifier": "bank_a_adapter_v1",
                "is_enabled": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "bank_code": "BNK_B",
                "display_name": "Beacon Commercial Bank",
                "adapter_identifier": "bank_b_adapter_v1",
                "is_enabled": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "bank_code": "BNK_C",
                "display_name": "Crestline Trust",
                "adapter_identifier": "bank_c_adapter_v1",
                "is_enabled": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "bank_code": "BNK_D",
                "display_name": "Delta Direct",
                "adapter_identifier": "bank_d_adapter_v1",
                "is_enabled": True,
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("ground_truth_labels")
    op.drop_table("transactions")
    op.drop_table("scenario_runs")
    op.drop_table("accounts")
    op.drop_table("banks")

