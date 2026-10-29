import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AccountRiskScore(Base):
    __tablename__ = "risk_scores"

    __table_args__ = (
        UniqueConstraint("scenario_run_id", "account_id", "detector_version", name="uq_run_account_detector"),
        Index("ix_risk_scores_run_id", "scenario_run_id"),
        Index("ix_risk_scores_account_id", "account_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    domain: Mapped[str] = mapped_column(String(32), default="current_money", nullable=False)
    scenario_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    risk_score: Mapped[Decimal] = mapped_column(Numeric(6, 2, asdecimal=True), nullable=False)
    risk_band: Mapped[str] = mapped_column(String(16), nullable=False)  # HIGH, MEDIUM, LOW
    signals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    scenario_run = relationship("ScenarioRun")
    account = relationship("Account")

