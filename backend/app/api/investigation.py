from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.investigation import (
    CytoscapeGraphResponse,
    RankingsResponse,
    FIFOAttributionItem,
)
from app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigation", tags=["Investigation"])


@router.get("/graph", response_model=CytoscapeGraphResponse)
def get_investigation_graph(
    scenario_run_id: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    max_depth: int = Query(3, ge=1, le=6),
    db: Session = Depends(get_db),
):
    """Retrieves Cytoscape graph nodes and distinct transaction edges.
    Supports forward and backward multi-hop expansion.
    """
    if not scenario_run_id and not case_id and not account_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide at least one of scenario_run_id, case_id, or account_id",
        )

    svc = InvestigationService(db)
    graph_data = svc.build_investigation_graph(
        scenario_run_id=scenario_run_id,
        case_id=case_id,
        account_id=account_id,
        max_depth=max_depth,
    )
    return CytoscapeGraphResponse(
        nodes=graph_data["nodes"],
        edges=graph_data["edges"],
    )


@router.get("/rankings", response_model=RankingsResponse)
def get_rankings(scenario_run_id: str, db: Session = Depends(get_db)):
    """Computes explainable ranking for suspected mules and potential coordinating kingpins."""
    svc = InvestigationService(db)
    rankings = svc.compute_mule_and_kingpin_rankings(scenario_run_id)
    return RankingsResponse(
        kingpins=rankings["kingpins"],
        mules=rankings["mules"],
    )


@router.get("/fifo-attribution", response_model=List[FIFOAttributionItem])
def get_fifo_attribution(scenario_run_id: str, db: Session = Depends(get_db)):
    """Computes deterministic FIFO fund attribution traces for transaction chains."""
    svc = InvestigationService(db)
    return svc.compute_fifo_fund_attribution(scenario_run_id)

