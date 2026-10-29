import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CBDCWallet(Base):
    __tablename__ = "cbdc_wallets"

    __table_args__ = (
        Index("ix_cbdc_wallets_address", "wallet_address"),
        Index("ix_cbdc_wallets_type", "wallet_type"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    wallet_address: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    wallet_type: Mapped[str] = mapped_column(String(32), nullable=False)  # ISSUER, INDIVIDUAL, MERCHANT, INTERMEDIARY
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 4, asdecimal=True), default=Decimal("0.0000"), nullable=False)
    synthetic_classification: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    token_lots = relationship("CBDCTokenLot", back_populates="current_holder_wallet")


class CBDCTokenLot(Base):
    __tablename__ = "cbdc_token_lots"

    __table_args__ = (
        Index("ix_cbdc_token_lots_holder", "current_holder_wallet_id"),
        Index("ix_cbdc_token_lots_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    lot_reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    current_holder_wallet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cbdc_wallets.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4, asdecimal=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)  # ACTIVE, SPENT, MERGED
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
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

    current_holder_wallet = relationship("CBDCWallet", back_populates="token_lots")


class CBDCLedgerEvent(Base):
    __tablename__ = "cbdc_ledger_events"

    __table_args__ = (
        Index("ix_cbdc_events_scenario_run", "scenario_run_id"),
        Index("ix_cbdc_events_from_wallet", "from_wallet_id"),
        Index("ix_cbdc_events_to_wallet", "to_wallet_id"),
        Index("ix_cbdc_events_timestamp", "event_timestamp"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scenario_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)  # ISSUANCE, TRANSFER, SPLIT, MERGE
    from_wallet_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cbdc_wallets.id", ondelete="RESTRICT"), nullable=True
    )
    to_wallet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cbdc_wallets.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4, asdecimal=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    parent_lot_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    child_lot_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    from_wallet = relationship("CBDCWallet", foreign_keys=[from_wallet_id])
    to_wallet = relationship("CBDCWallet", foreign_keys=[to_wallet_id])
    scenario_run = relationship("ScenarioRun")


class CBDCGroundTruth(Base):
    __tablename__ = "cbdc_ground_truth"

    __table_args__ = (
        Index("ix_cbdc_gt_run", "scenario_run_id"),
        Index("ix_cbdc_gt_wallet", "wallet_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scenario_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False
    )
    wallet_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cbdc_wallets.id", ondelete="CASCADE"), nullable=True
    )
    event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cbdc_ledger_events.id", ondelete="CASCADE"), nullable=True
    )
    role_label: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_relationship: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    scenario_run = relationship("ScenarioRun")
    wallet = relationship("CBDCWallet")
    event = relationship("CBDCLedgerEvent")

