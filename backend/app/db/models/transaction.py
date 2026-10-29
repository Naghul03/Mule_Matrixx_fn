import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    JSON,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    __table_args__ = (
        CheckConstraint(
            "source_account_id <> destination_account_id",
            name="ck_transactions_no_self_transfer",
        ),
        UniqueConstraint(
            "originating_bank_id",
            "native_transaction_reference",
            name="uq_transactions_bank_native_ref",
        ),
        Index("ix_transactions_scenario_run", "scenario_run_id"),
        Index("ix_transactions_origin_bank", "originating_bank_id"),
        Index("ix_transactions_source_acc", "source_account_id"),
        Index("ix_transactions_dest_acc", "destination_account_id"),
        Index("ix_transactions_event_time", "event_timestamp"),
        Index("ix_transactions_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scenario_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="SET NULL"), nullable=True
    )
    originating_bank_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("banks.id", ondelete="RESTRICT"), nullable=False
    )
    source_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    destination_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4, asdecimal=True), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    native_transaction_reference: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    normalized_type: Mapped[str] = mapped_column(
        String(32), default="TRANSFER", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(24), default="COMPLETED", nullable=False
    )
    source_adapter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalization_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    scenario_run: Mapped["ScenarioRun | None"] = relationship(  # type: ignore # noqa: F821
        "ScenarioRun", back_populates="transactions"
    )
    originating_bank: Mapped["Bank"] = relationship(  # type: ignore # noqa: F821
        "Bank", back_populates="originated_transactions"
    )
    source_account: Mapped["Account"] = relationship(  # type: ignore # noqa: F821
        "Account",
        foreign_keys=[source_account_id],
        back_populates="outgoing_transactions",
    )
    destination_account: Mapped["Account"] = relationship(  # type: ignore # noqa: F821
        "Account",
        foreign_keys=[destination_account_id],
        back_populates="incoming_transactions",
    )

    def __repr__(self) -> str:
        return f"<Transaction(id='{self.id}', amount={self.amount} {self.currency}, time='{self.event_timestamp}')>"

