from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models.scenario_run import ScenarioRun
from app.db.models.transaction import Transaction
from app.db.models.alert import Alert
from app.db.models.case import Case
from app.schemas.scenario import (
    ScenarioRunRequest,
    ScenarioTemplate,
    ScenarioRunResponse,
)
from app.services.scenario_generator import ScenarioGeneratorService
from app.services.detection_service import DetectionService
from app.services.cbdc_service import CBDCService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

TEMPLATES = [
    ScenarioTemplate(
        id="scenario_1",
        name="Scenario 1: Conventional Money Tracing",
        domain="current_money",
        description="Linear and branching pass-through money movement from a victim account through sequential intermediary mule accounts toward a coordinating kingpin.",
        default_seed=42,
        default_amount=Decimal("500000.00"),
        key_typologies=["Rapid Pass-Through", "Linear Layering", "Terminal Aggregation"],
    ),
    ScenarioTemplate(
        id="scenario_3",
        name="Scenario 3: Pre-Positioned Transfers & Delayed Replenishment",
        domain="current_money",
        description="High-priority multi-day coordinated topology where nodes B and C pre-fund D on Day 0, Victim transfers to A on Day 2, and A provides delayed replenishment to B and C on Day 3.",
        default_seed=1337,
        default_amount=Decimal("400000.00"),
        key_typologies=["Historical Pre-Positioning", "Delayed Replenishment", "Asymmetric Coordination"],
    ),
    ScenarioTemplate(
        id="scenario_4",
        name="Scenario 4: Fragmented Structuring (Smurfing)",
        domain="current_money",
        description="Coordinated sub-threshold fragmented transfers (₹1,20,000 x 8 transfers = ₹9,60,000) dispersed across smurf accounts converging upon a central collector account.",
        default_seed=8080,
        default_amount=Decimal("120000.00"),
        key_typologies=["Smurfing / Structuring", "Fan-In Aggregation", "Sub-Threshold Evasion"],
    ),
    ScenarioTemplate(
        id="scenario_2",
        name="Scenario 2: CBDC Token Lineage & Provenance",
        domain="cbdc",
        description="Simulated Central Bank Digital Currency token lot issuance, lot splitting into fragments, multi-wallet transmission, and consolidation merge into a coordinating wallet.",
        default_seed=2026,
        default_amount=Decimal("1000000.00"),
        key_typologies=["Token Lot Splitting", "Parent-Child Lineage", "Mixer / Merging"],
    ),
]


@router.get("", response_model=List[ScenarioTemplate])
def list_scenario_templates(domain: Optional[str] = Query(None)):
    """Returns available simulation scenario templates."""
    if domain:
        return [t for t in TEMPLATES if t.domain == domain]
    return TEMPLATES


@router.post("/run", response_model=ScenarioRunResponse, status_code=status.HTTP_201_CREATED)
def run_scenario(req: ScenarioRunRequest, db: Session = Depends(get_db)):
    """Executes a scenario run, validates against 4 bank adapters, persists transactions, and triggers detection."""
    if req.scenario_id == "scenario_2":
        # CBDC Scenario
        cbdc_svc = CBDCService(db)
        run = cbdc_svc.generate_scenario_2(
            seed=req.seed,
            base_amount=req.base_amount,
            num_intermediaries=req.num_attack_accounts,
        )
    else:
        # Current Money Scenarios
        svc = ScenarioGeneratorService(db)
        run = svc.generate_scenario(
            scenario_id=req.scenario_id,
            seed=req.seed,
            base_amount=req.base_amount,
            num_attack_accounts=req.num_attack_accounts,
            num_decoys=req.num_decoys,
            custom_config=req.custom_config,
        )

        # Trigger automatic detection over the newly generated transactions
        detector = DetectionService(db)
        detector.analyze_scenario_run(run.id, domain=run.domain)

    # Fetch counts
    tx_count = db.execute(select(func.count(Transaction.id)).where(Transaction.scenario_run_id == run.id)).scalar() or 0
    al_count = db.execute(select(func.count(Alert.id)).where(Alert.scenario_run_id == run.id)).scalar() or 0
    cs_count = db.execute(select(func.count(Case.id)).where(Case.scenario_run_id == run.id)).scalar() or 0

    return ScenarioRunResponse(
        id=run.id,
        domain=run.domain,
        scenario_identifier=run.scenario_identifier,
        scenario_version=run.scenario_version,
        generator_version=run.generator_version,
        seed=run.seed,
        status=run.status,
        configuration_json=run.configuration_json,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        transaction_count=tx_count,
        alert_count=al_count,
        case_count=cs_count,
    )


@router.get("/runs", response_model=List[ScenarioRunResponse])
def list_scenario_runs(
    domain: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists historical scenario runs with execution metadata and entity counts."""
    query = select(ScenarioRun).order_by(ScenarioRun.created_at.desc())
    if domain:
        query = query.where(ScenarioRun.domain == domain)

    runs = list(db.execute(query.limit(limit)).scalars().all())

    results = []
    for r in runs:
        tx_count = db.execute(select(func.count(Transaction.id)).where(Transaction.scenario_run_id == r.id)).scalar() or 0
        al_count = db.execute(select(func.count(Alert.id)).where(Alert.scenario_run_id == r.id)).scalar() or 0
        cs_count = db.execute(select(func.count(Case.id)).where(Case.scenario_run_id == r.id)).scalar() or 0

        results.append(
            ScenarioRunResponse(
                id=r.id,
                domain=r.domain,
                scenario_identifier=r.scenario_identifier,
                scenario_version=r.scenario_version,
                generator_version=r.generator_version,
                seed=r.seed,
                status=r.status,
                configuration_json=r.configuration_json,
                started_at=r.started_at,
                completed_at=r.completed_at,
                created_at=r.created_at,
                transaction_count=tx_count,
                alert_count=al_count,
                case_count=cs_count,
            )
        )
    return results


@router.get("/runs/{run_id}", response_model=ScenarioRunResponse)
def get_scenario_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(ScenarioRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Scenario run not found")

    tx_count = db.execute(select(func.count(Transaction.id)).where(Transaction.scenario_run_id == run.id)).scalar() or 0
    al_count = db.execute(select(func.count(Alert.id)).where(Alert.scenario_run_id == run.id)).scalar() or 0
    cs_count = db.execute(select(func.count(Case.id)).where(Case.scenario_run_id == run.id)).scalar() or 0

    return ScenarioRunResponse(
        id=run.id,
        domain=run.domain,
        scenario_identifier=run.scenario_identifier,
        scenario_version=run.scenario_version,
        generator_version=run.generator_version,
        seed=run.seed,
        status=run.status,
        configuration_json=run.configuration_json,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        transaction_count=tx_count,
        alert_count=al_count,
        case_count=cs_count,
    )

