import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    __table_args__ = (
        Index("ix_eval_runs_scenario_run_id", "scenario_run_id"),
        Index("ix_eval_runs_domain", "domain"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    domain: Mapped[str] = mapped_column(String(32), default="current_money", nullable=False)
    scenario_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False
    )
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    baseline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    seed_type: Mapped[str] = mapped_column(String(16), nullable=False)  # DEVELOPMENT, VALIDATION, HOLDOUT
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    baseline_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    confusion_matrix: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    baseline_confusion_matrix: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    scenario_run = relationship("ScenarioRun")

