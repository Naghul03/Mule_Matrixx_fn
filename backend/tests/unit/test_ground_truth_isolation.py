from app.schemas.canonical import CanonicalTransaction
from app.schemas.account import AccountRead
from app.schemas.bank import BankRead


def test_canonical_transaction_has_no_ground_truth_fields():
    """Ensure detector-facing CanonicalTransaction schema strictly excludes hidden ground truth."""
    fields = CanonicalTransaction.model_fields.keys()
    forbidden_terms = [
        "ground_truth",
        "role_label",
        "is_mule",
        "attack_role",
        "rationale",
        "expected_relationship",
        "malicious",
        "label",
    ]
    for field in fields:
        for term in forbidden_terms:
            assert term not in field.lower(), f"Forbidden ground truth term '{term}' found in transaction schema field '{field}'"


def test_account_read_has_no_ground_truth_fields():
    """Ensure standard account schema does not expose synthetic classifications or labels."""
    fields = AccountRead.model_fields.keys()
    assert "synthetic_classification" not in fields
    assert "role_label" not in fields
    assert "is_mule" not in fields


def test_bank_read_has_no_ground_truth_fields():
    fields = BankRead.model_fields.keys()
    assert "is_compromised" not in fields
    assert "ground_truth" not in fields

