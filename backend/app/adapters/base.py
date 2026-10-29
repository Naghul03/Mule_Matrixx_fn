from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.schemas.canonical import CanonicalTransaction


class BankAdapterValidationError(ValueError):
    """Raised when native banking payload fails schema or business invariant validation."""

    def __init__(
        self,
        adapter: str,
        field: str,
        reason: str,
        raw_value: Optional[Any] = None,
    ):
        self.adapter = adapter
        self.field = field
        self.reason = reason
        self.raw_value = raw_value
        super().__init__(
            f"[{adapter}] Validation failed on field '{field}': {reason} (Received: {raw_value!r})"
        )


class BaseBankAdapter(ABC):
    """Abstract Base Class for simulated bank transaction adapters."""

    @property
    @abstractmethod
    def bank_code(self) -> str:
        """The standard bank code handled by this adapter (e.g. 'BNK_A')."""
        ...

    @property
    @abstractmethod
    def adapter_version(self) -> str:
        """The identifier and version of this adapter (e.g. 'bank_a_adapter_v1')."""
        ...

    @abstractmethod
    def normalize(self, raw_record: Dict[str, Any]) -> CanonicalTransaction:
        """Validate and normalize a bank's native payload into a CanonicalTransaction.

        Raises:
            BankAdapterValidationError: If validation fails or fields are missing/malformed.
        """
        ...

