import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Case(Base):
    __tablename__ = "cases"

    __table_args__ = (
        Index("ix_cases_domain", "domain"),
        Index("ix_cases_status", "status"),
        Index("ix_cases_priority", "priority"),
        Index("ix_cases_scenario_run_id", "scenario_run_id"),
        Index("ix_cases_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(32), default="current_money", nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="OPEN", nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    risk_band: Mapped[str | None] = mapped_column(String(16), nullable=True)
    aggregate_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2, asdecimal=True), nullable=True)
    scenario_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="SET NULL"), nullable=True
    )
    is_manual_entry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manual_entry_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    scenario_run = relationship("ScenarioRun")
    alerts = relationship("CaseAlert", back_populates="case", cascade="all, delete-orphan")
    accounts = relationship("CaseAccount", back_populates="case", cascade="all, delete-orphan")
    transactions = relationship("CaseTransaction", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan", order_by="CaseNote.created_at.desc()")


class CaseAlert(Base):
    __tablename__ = "case_alerts"

    __table_args__ = (
        UniqueConstraint("case_id", "alert_id", name="uq_case_alert"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = relationship("Case", back_populates="alerts")
    alert = relationship("Alert", back_populates="case_associations")


class CaseAccount(Base):
    __tablename__ = "case_accounts"

    __table_args__ = (
        UniqueConstraint("case_id", "account_id", name="uq_case_account"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str | None] = mapped_column(String(32), nullable=True)  # suspect, victim, intermediary, kingpin_candidate, witness
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = relationship("Case", back_populates="accounts")
    account = relationship("Account")


class CaseTransaction(Base):
    __tablename__ = "case_transactions"

    __table_args__ = (
        UniqueConstraint("case_id", "transaction_id", name="uq_case_transaction"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(32), default="DIRECT", nullable=False)  # DIRECT, HISTORICAL, INFERRED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = relationship("Case", back_populates="transactions")
    transaction = relationship("Transaction")


class CaseNote(Base):
    __tablename__ = "case_notes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    note_type: Mapped[str] = mapped_column(String(24), nullable=False)  # STATUS_CHANGE, INVESTIGATION_NOTE, EVIDENCE_ADDED, SYSTEM
    content: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = relationship("Case", back_populates="notes")

