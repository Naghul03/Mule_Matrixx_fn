import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class GroundTruthLabel(Base):
    """Hidden ground truth evaluation model.

    STRICT ISOLATION POLICY:
    This model and its underlying table are strictly reserved for post-detection
    evaluation and benchmarking (Module 5 / 7).
    The detector, feature extraction pipelines, and standard transaction API
    endpoints must NEVER query or join with this table.
    """
    __tablename__ = "ground_truth_labels"

    __table_args__ = (
        Index("ix_gt_scenario_run", "scenario_run_id"),
        Index("ix_gt_account_id", "account_id"),
        Index("ix_gt_transaction_id", "transaction_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scenario_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True
    )
    transaction_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True
    )
    role_label: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_relationship: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    scenario_run: Mapped["ScenarioRun"] = relationship(  # type: ignore # noqa: F821
        "ScenarioRun", back_populates="ground_truth_labels"
    )

    def __repr__(self) -> str:
        return f"<GroundTruthLabel(run='{self.scenario_run_id}', role='{self.role_label}')>"

