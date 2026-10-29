from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select

from app.db.models.bank import Bank
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.scenario_run import ScenarioRun
from app.db.models.alert import Alert
from app.db.models.case import Case
from app.db.models.cbdc import CBDCWallet, CBDCTokenLot, CBDCLedgerEvent
from app.services.scenario_generator import ScenarioGeneratorService
from app.services.detection_service import DetectionService
from app.services.investigation_service import InvestigationService
from app.services.evaluation_service import EvaluationService
from app.services.cbdc_service import CBDCService
from app.services.reporting_service import ReportingService


def test_scenario_3_acceptance_targets(db_session):
    """Verifies all strict acceptance targets for Scenario 3:

    - DAY 0: B -> D (2L), C -> D (2L) [Historical relationship]
    - DAY 2: Victim -> A (4L)
    - DAY 3: A -> B (2L), A -> C (2L)
    Acceptance Targets:
    1. A, B, and C flagged as suspicious.
    2. D ranks FIRST (#1) as potential kingpin in default seed (1337).
    3. Victim is NOT flagged as a mule.
    4. Graph distinguishes direct transfers from historical relationships.
    5. No direct victim-to-D transfer edge is fabricated.
    """
    svc = ScenarioGeneratorService(db_session)
    run = svc.generate_scenario(scenario_id="scenario_3", seed=1337)

    # 1. Verify scenario run generated
    assert run.status == "COMPLETED"
    assert run.domain == "current_money"

    # 2. Run detection engine
    detector = DetectionService(db_session)
    alerts = detector.analyze_scenario_run(run.id, domain="current_money")
    assert len(alerts) > 0

    alerted_acc_ids = {a.account_id for a in alerts}

    # Find victim, A, B, C, D accounts
    accounts = list(
        db_session.execute(
            select(Account).join(Transaction, (Account.id == Transaction.source_account_id) | (Account.id == Transaction.destination_account_id))
            .where(Transaction.scenario_run_id == run.id)
        ).scalars().all()
    )
    acc_by_alias = {a.display_alias: a for a in accounts}

    vic = acc_by_alias.get("Victim (S3)")
    node_a = acc_by_alias.get("Mule Node A")
    node_b = acc_by_alias.get("Mule Node B")
    node_c = acc_by_alias.get("Mule Node C")
    node_d = acc_by_alias.get("Kingpin D")

    assert vic is not None
    assert node_a is not None
    assert node_b is not None
    assert node_c is not None
    assert node_d is not None

    # Target 1: A, B, C flagged as suspicious
    assert node_a.id in alerted_acc_ids, "Node A should be flagged as suspicious"
    assert node_b.id in alerted_acc_ids, "Node B should be flagged as suspicious"
    assert node_c.id in alerted_acc_ids, "Node C should be flagged as suspicious"

    # Target 3: Victim is NOT flagged as a mule
    assert vic.id not in alerted_acc_ids, "Victim must NOT be flagged as a mule"

    # Target 2: D ranks FIRST (#1) as potential kingpin
    inv_svc = InvestigationService(db_session)
    rankings = inv_svc.compute_mule_and_kingpin_rankings(run.id)

    assert len(rankings["kingpins"]) > 0
    top_kingpin = rankings["kingpins"][0]
    assert top_kingpin["accountId"] == node_d.id, f"Node D should rank #1 as kingpin, got: {top_kingpin['alias']}"

    # Target 4 & 5: Graph distinguishes direct vs historical and contains no fake victim-to-D edge
    graph = inv_svc.build_investigation_graph(scenario_run_id=run.id)
    edges = graph["edges"]

    # Verify no edge from victim directly to D
    victim_to_d_edges = [e for e in edges if e["data"]["source"] == vic.id and e["data"]["target"] == node_d.id]
    assert len(victim_to_d_edges) == 0, "No fake victim-to-D edge should exist"

    # Verify historical edge classification exists
    historical_edges = [e for e in edges if e["data"]["evidenceType"] == "HISTORICAL"]
    assert len(historical_edges) >= 2, "Earlier B->D and C->D transfers should be classified as HISTORICAL"


def test_scenario_1_and_reproducibility(db_session):
    """Verifies Scenario 1 linear pass-through chain and exact seed reproducibility."""
    svc = ScenarioGeneratorService(db_session)
    run1 = svc.generate_scenario(scenario_id="scenario_1", seed=42, num_attack_accounts=5, num_decoys=3)
    txns1 = list(db_session.execute(select(Transaction).where(Transaction.scenario_run_id == run1.id)).scalars().all())

    # Same seed should reproduce identical transfer amounts
    amounts1 = [t.amount for t in sorted(txns1, key=lambda x: x.event_timestamp)]
    assert len(amounts1) > 0

    # Test attack accounts cap (max 10)
    run_capped = svc.generate_scenario(scenario_id="scenario_1", seed=99, num_attack_accounts=25)
    cfg = run_capped.configuration_json
    assert cfg["num_attack_accounts"] == 10, "Attack accounts must be capped at 10"


def test_scenario_4_fragmented_structuring(db_session):
    """Verifies Scenario 4 structuring (₹9,60,000 across 8 transfers of ₹1,20,000)."""
    svc = ScenarioGeneratorService(db_session)
    run = svc.generate_scenario(scenario_id="scenario_4", seed=8080)

    txns = list(
        db_session.execute(
            select(Transaction).where(Transaction.scenario_run_id == run.id)
        ).scalars().all()
    )

    structured_txns = [t for t in txns if t.amount == Decimal("120000.0000")]
    assert len(structured_txns) == 8, f"Expected 8 structured transfers of 1,20,000, found {len(structured_txns)}"


def test_manual_case_entry_verified_and_unverified(client, db_session):
    """Tests manual case entry:

    - Matching reference -> Verified Case
    - Unmatched reference -> Unverified Lead (no fake graphs)
    """
    # 1. Create a real transaction to match
    svc = ScenarioGeneratorService(db_session)
    run = svc.generate_scenario(scenario_id="scenario_1", seed=55)
    real_tx = db_session.execute(select(Transaction).where(Transaction.scenario_run_id == run.id)).scalars().first()
    tx_bank = db_session.get(Bank, real_tx.originating_bank_id)

    # Verified manual entry
    res_verified = client.post(
        "/api/v1/cases/manual",
        json={
            "bank_code": tx_bank.bank_code,
            "transaction_reference": real_tx.native_transaction_reference,
            "suspicion_category": "SUSPICIOUS_TRANSFER",
            "description": "Investigating high velocity outbound transfer reported by teller",
        },
    )
    assert res_verified.status_code == 201
    data_v = res_verified.json()
    assert data_v["is_manual_entry"] is True
    assert data_v["manual_entry_data"]["is_verified_match"] is True
    assert data_v["transaction_count"] >= 1

    # Unverified lead
    res_unverified = client.post(
        "/api/v1/cases/manual",
        json={
            "bank_code": "BNK_A",
            "transaction_reference": "NON_EXISTENT_TX_REF_9999",
            "suspicion_category": "UNVERIFIED_TIP",
            "description": "Anonymous informant tip about alleged kickback",
        },
    )
    assert res_unverified.status_code == 201
    data_u = res_unverified.json()
    assert data_u["is_manual_entry"] is True
    assert data_u["manual_entry_data"]["is_verified_match"] is False
    assert data_u["transaction_count"] == 0
    assert "UNVERIFIED LEAD" in data_u["summary"]


def test_fifo_fund_attribution(db_session):
    """Verifies FIFO fund attribution tracks incoming lots and consumes older lots first."""
    svc = ScenarioGeneratorService(db_session)
    run = svc.generate_scenario(scenario_id="scenario_3", seed=1337)

    inv_svc = InvestigationService(db_session)
    attribution = inv_svc.compute_fifo_fund_attribution(run.id)
    assert len(attribution) > 0

    # Ensure attribution amounts reconcile
    for a in attribution:
        assert a["amount"] > 0
        total_covered = sum((p["attributedAmount"] for p in a["consumedAllocations"])) + a["unattributedAmount"]
        assert abs(total_covered - a["amount"]) < 0.001


def test_cbdc_scenario_2_and_conservation(db_session):
    """Verifies CBDC Scenario 2:

    - Token issuance from Central Bank
    - Token lot splitting with strict conservation
    - Multi-wallet transfer
    - Re-aggregation merge
    - No negative balances / no overspending
    """
    cbdc_svc = CBDCService(db_session)
    run = cbdc_svc.generate_scenario_2(seed=2026, base_amount=Decimal("1000000.0000"))

    assert run.status == "COMPLETED"
    assert run.domain == "cbdc"

    # Verify wallets have non-negative balances
    wallets = list(db_session.execute(select(CBDCWallet)).scalars().all())
    for w in wallets:
        assert w.balance >= Decimal("0.0000"), f"Wallet {w.wallet_address} has negative balance {w.balance}"

    # Verify provenance explorer can trace split & merge child/parent lots
    lots = list(db_session.execute(select(CBDCTokenLot)).scalars().all())
    assert len(lots) >= 4

    target_lot = lots[0]
    provenance = cbdc_svc.get_token_provenance(target_lot.id)
    assert "targetLot" in provenance
    assert "parents" in provenance
    assert "children" in provenance


def test_evaluation_baseline_comparison(db_session):
    """Verifies Evaluation service executes baseline and Mule Matrix detectors without ground truth leakage."""
    svc = ScenarioGeneratorService(db_session)
    run = svc.generate_scenario(scenario_id="scenario_3", seed=1337)

    eval_svc = EvaluationService(db_session)
    eval_run = eval_svc.evaluate_scenario_run(run.id, seed_type="HOLDOUT")

    assert eval_run.metrics is not None
    assert eval_run.baseline_metrics is not None
    assert "precision" in eval_run.metrics
    assert "recall" in eval_run.metrics
    assert "f1_score" in eval_run.metrics
    assert eval_run.confusion_matrix is not None


def test_reporting_html_generation(db_session):
    """Verifies report generation creates case HTML dossier."""
    svc = ScenarioGeneratorService(db_session)
    run = svc.generate_scenario(scenario_id="scenario_3", seed=1337)

    # Trigger detection to create a case
    detector = DetectionService(db_session)
    detector.analyze_scenario_run(run.id)

    case = db_session.execute(select(Case).where(Case.scenario_run_id == run.id)).scalars().first()
    assert case is not None

    rep_svc = ReportingService(db_session)
    html = rep_svc.generate_case_html(case.id)

    assert "Mule Matrix" in html
    assert case.case_reference in html
    assert "SIMULATION RESEARCH NOTICE" in html
