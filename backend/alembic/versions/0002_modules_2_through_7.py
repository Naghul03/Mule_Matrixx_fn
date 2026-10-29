"""Modules 2 through 7 schema extensions

Revision ID: 0002_modules_2_through_7
Revises: 0001_initial_foundation
Create Date: 2026-10-29 03:00:00.000000 UTC

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_modules_2_through_7"
down_revision: Union[str, None] = "0001_initial_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alerts Table
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain", sa.String(32), nullable=False, server_default="current_money"),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("transaction_id", sa.String(36), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("risk_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("risk_band", sa.String(16), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("detector_version", sa.String(32), nullable=False),
        sa.Column("review_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_domain", "alerts", ["domain"])
    op.create_index("ix_alerts_scenario_run_id", "alerts", ["scenario_run_id"])
    op.create_index("ix_alerts_account_id", "alerts", ["account_id"])
    op.create_index("ix_alerts_risk_band", "alerts", ["risk_band"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])

    # 2. Cases Table
    op.create_table(
        "cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_reference", sa.String(32), unique=True, nullable=False),
        sa.Column("domain", sa.String(32), nullable=False, server_default="current_money"),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="OPEN"),
        sa.Column("priority", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("risk_band", sa.String(16), nullable=True),
        sa.Column("aggregate_risk_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_manual_entry", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("manual_entry_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cases_domain", "cases", ["domain"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_priority", "cases", ["priority"])
    op.create_index("ix_cases_scenario_run_id", "cases", ["scenario_run_id"])
    op.create_index("ix_cases_created_at", "cases", ["created_at"])

    # 3. Case-Alerts Association
    op.create_table(
        "case_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "alert_id", name="uq_case_alert"),
    )
    op.create_index("ix_case_alerts_case_id", "case_alerts", ["case_id"])
    op.create_index("ix_case_alerts_alert_id", "case_alerts", ["alert_id"])

    # 4. Case-Accounts Association
    op.create_table(
        "case_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "account_id", name="uq_case_account"),
    )
    op.create_index("ix_case_accounts_case_id", "case_accounts", ["case_id"])
    op.create_index("ix_case_accounts_account_id", "case_accounts", ["account_id"])

    # 5. Case-Transactions Association
    op.create_table(
        "case_transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_id", sa.String(36), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(32), nullable=False, server_default="DIRECT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "transaction_id", name="uq_case_transaction"),
    )
    op.create_index("ix_case_txns_case_id", "case_transactions", ["case_id"])
    op.create_index("ix_case_txns_txn_id", "case_transactions", ["transaction_id"])

    # 6. Case Notes & Audit History
    op.create_table(
        "case_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note_type", sa.String(24), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("previous_status", sa.String(24), nullable=True),
        sa.Column("new_status", sa.String(24), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id"])

    # 7. Risk Scores Table
    op.create_table(
        "risk_scores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain", sa.String(32), nullable=False, server_default="current_money"),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("risk_band", sa.String(16), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("detector_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("scenario_run_id", "account_id", "detector_version", name="uq_run_account_detector"),
    )
    op.create_index("ix_risk_scores_run_id", "risk_scores", ["scenario_run_id"])
    op.create_index("ix_risk_scores_account_id", "risk_scores", ["account_id"])

    # 8. Evaluation Runs Table
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain", sa.String(32), nullable=False, server_default="current_money"),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("detector_version", sa.String(32), nullable=False),
        sa.Column("baseline_version", sa.String(32), nullable=False),
        sa.Column("seed_type", sa.String(16), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("baseline_metrics", sa.JSON(), nullable=False),
        sa.Column("confusion_matrix", sa.JSON(), nullable=True),
        sa.Column("baseline_confusion_matrix", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_runs_scenario_run_id", "evaluation_runs", ["scenario_run_id"])
    op.create_index("ix_eval_runs_domain", "evaluation_runs", ["domain"])

    # 9. CBDC Wallets Table
    op.create_table(
        "cbdc_wallets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("wallet_address", sa.String(64), unique=True, nullable=False),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("wallet_type", sa.String(32), nullable=False),
        sa.Column("balance", sa.Numeric(18, 4), nullable=False, server_default="0.0000"),
        sa.Column("synthetic_classification", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cbdc_wallets_address", "cbdc_wallets", ["wallet_address"])
    op.create_index("ix_cbdc_wallets_type", "cbdc_wallets", ["wallet_type"])

    # 10. CBDC Token Lots Table
    op.create_table(
        "cbdc_token_lots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lot_reference", sa.String(64), unique=True, nullable=False),
        sa.Column("current_holder_wallet_id", sa.String(36), sa.ForeignKey("cbdc_wallets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("origin_event_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cbdc_token_lots_holder", "cbdc_token_lots", ["current_holder_wallet_id"])
    op.create_index("ix_cbdc_token_lots_status", "cbdc_token_lots", ["status"])

    # 11. CBDC Ledger Events Table
    op.create_table(
        "cbdc_ledger_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(16), nullable=False),
        sa.Column("from_wallet_id", sa.String(36), sa.ForeignKey("cbdc_wallets.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("to_wallet_id", sa.String(36), sa.ForeignKey("cbdc_wallets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parent_lot_ids", sa.JSON(), nullable=True),
        sa.Column("child_lot_ids", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cbdc_events_scenario_run", "cbdc_ledger_events", ["scenario_run_id"])
    op.create_index("ix_cbdc_events_from_wallet", "cbdc_ledger_events", ["from_wallet_id"])
    op.create_index("ix_cbdc_events_to_wallet", "cbdc_ledger_events", ["to_wallet_id"])
    op.create_index("ix_cbdc_events_timestamp", "cbdc_ledger_events", ["event_timestamp"])

    # 12. CBDC Ground Truth Labels Table
    op.create_table(
        "cbdc_ground_truth",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scenario_run_id", sa.String(36), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wallet_id", sa.String(36), sa.ForeignKey("cbdc_wallets.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("cbdc_ledger_events.id", ondelete="CASCADE"), nullable=True),
        sa.Column("role_label", sa.String(64), nullable=False),
        sa.Column("expected_relationship", sa.String(64), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cbdc_gt_run", "cbdc_ground_truth", ["scenario_run_id"])
    op.create_index("ix_cbdc_gt_wallet", "cbdc_ground_truth", ["wallet_id"])


def downgrade() -> None:
    op.drop_table("cbdc_ground_truth")
    op.drop_table("cbdc_ledger_events")
    op.drop_table("cbdc_token_lots")
    op.drop_table("cbdc_wallets")
    op.drop_table("evaluation_runs")
    op.drop_table("risk_scores")
    op.drop_table("case_notes")
    op.drop_table("case_transactions")
    op.drop_table("case_accounts")
    op.drop_table("case_alerts")
    op.drop_table("cases")
    op.drop_table("alerts")

