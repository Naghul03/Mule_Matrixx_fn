import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        Index("ix_alerts_domain", "domain"),
        Index("ix_alerts_scenario_run_id", "scenario_run_id"),
        Index("ix_alerts_account_id", "account_id"),
        Index("ix_alerts_risk_band", "risk_band"),
        Index("ix_alerts_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    domain: Mapped[str] = mapped_column(String(32), default="current_money", nullable=False)
    scenario_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=True
    )
    account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True
    )
    transaction_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True
    )
    risk_score: Mapped[Decimal] = mapped_column(Numeric(6, 2, asdecimal=True), nullable=False)
    risk_band: Mapped[str] = mapped_column(String(16), nullable=False)
    signals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    review_status: Mapped[str] = mapped_column(String(24), default="PENDING", nullable=False)

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
    account = relationship("Account")
    transaction = relationship("Transaction")
    case_associations = relationship("CaseAlert", back_populates="alert", cascade="all, delete-orphan")

