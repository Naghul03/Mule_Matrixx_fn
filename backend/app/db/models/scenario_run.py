import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, BigInteger, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    domain: Mapped[str] = mapped_column(String(32), default="current_money", index=True, nullable=False)
    scenario_identifier: Mapped[str] = mapped_column(String(64), nullable=False)
    scenario_version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)
    generator_version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    configuration_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(  # type: ignore # noqa: F821
        "Transaction", back_populates="scenario_run"
    )
    ground_truth_labels: Mapped[list["GroundTruthLabel"]] = relationship(  # type: ignore # noqa: F821
        "GroundTruthLabel", back_populates="scenario_run"
    )

    def __repr__(self) -> str:
        return f"<ScenarioRun(id='{self.id}', scenario='{self.scenario_identifier}', seed={self.seed})>"

