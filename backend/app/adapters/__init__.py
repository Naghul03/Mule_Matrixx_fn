from typing import Dict, Type
from app.adapters.base import BaseBankAdapter, BankAdapterValidationError
from app.adapters.bank_a import BankAAdapter
from app.adapters.bank_b import BankBAdapter
from app.adapters.bank_c import BankCAdapter
from app.adapters.bank_d import BankDAdapter

ADAPTER_REGISTRY: Dict[str, Type[BaseBankAdapter]] = {
    "BNK_A": BankAAdapter,
    "BNK_B": BankBAdapter,
    "BNK_C": BankCAdapter,
    "BNK_D": BankDAdapter,
}


def get_adapter_for_bank(bank_code: str) -> BaseBankAdapter:
    """Retrieve an initialized adapter instance by bank code."""
    code = bank_code.strip().upper()
    if code not in ADAPTER_REGISTRY:
        raise ValueError(
            f"No adapter registered for bank code '{bank_code}'. "
            f"Available adapters: {list(ADAPTER_REGISTRY.keys())}"
        )
    return ADAPTER_REGISTRY[code]()


__all__ = [
    "BaseBankAdapter",
    "BankAdapterValidationError",
    "BankAAdapter",
    "BankBAdapter",
    "BankCAdapter",
    "BankDAdapter",
    "ADAPTER_REGISTRY",
    "get_adapter_for_bank",
]

