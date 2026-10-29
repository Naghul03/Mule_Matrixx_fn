import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"

    __table_args__ = (
        UniqueConstraint("bank_id", "bank_account_reference", name="uq_accounts_bank_ref"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    bank_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("banks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    bank_account_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    display_alias: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Simulation-only classification (isolated from detector queries)
    synthetic_classification: Mapped[str | None] = mapped_column(String(64), nullable=True)

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
    bank: Mapped["Bank"] = relationship("Bank", back_populates="accounts")  # type: ignore # noqa: F821
    outgoing_transactions: Mapped[list["Transaction"]] = relationship(  # type: ignore # noqa: F821
        "Transaction",
        foreign_keys="Transaction.source_account_id",
        back_populates="source_account",
    )
    incoming_transactions: Mapped[list["Transaction"]] = relationship(  # type: ignore # noqa: F821
        "Transaction",
        foreign_keys="Transaction.destination_account_id",
        back_populates="destination_account",
    )

    def __repr__(self) -> str:
        return f"<Account(bank_id='{self.bank_id}', ref='{self.bank_account_reference}')>"

