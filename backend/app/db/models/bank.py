import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    bank_code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    adapter_identifier: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="bank")  # type: ignore # noqa: F821
    originated_transactions: Mapped[list["Transaction"]] = relationship(  # type: ignore # noqa: F821
        "Transaction", back_populates="originating_bank"
    )

    def __repr__(self) -> str:
        return f"<Bank(code='{self.bank_code}', name='{self.display_name}')>"

