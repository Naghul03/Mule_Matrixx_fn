from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.evaluation import EvaluationRun
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def run_evaluation(req: EvaluationRunRequest, db: Session = Depends(get_db)):
    """Executes evaluation comparing Mule Matrix detection against single-transaction baseline.
    Strict sequence: Ground truth is ONLY accessed after both detectors have finalized predictions.
    """
    svc = EvaluationService(db)
    eval_run = svc.evaluate_scenario_run(
        scenario_run_id=req.scenario_run_id,
        seed_type=req.seed_type,
        domain=req.domain,
    )
    return EvaluationRunResponse(
        id=eval_run.id,
        domain=eval_run.domain,
        scenario_run_id=eval_run.scenario_run_id,
        detector_version=eval_run.detector_version,
        baseline_version=eval_run.baseline_version,
        seed_type=eval_run.seed_type,
        metrics=eval_run.metrics,
        baseline_metrics=eval_run.baseline_metrics,
        confusion_matrix=eval_run.confusion_matrix,
        baseline_confusion_matrix=eval_run.baseline_confusion_matrix,
        created_at=eval_run.created_at,
    )


@router.get("/runs", response_model=List[EvaluationRunResponse])
def list_evaluation_runs(
    domain: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = select(EvaluationRun).order_by(EvaluationRun.created_at.desc())
    if domain:
        query = query.where(EvaluationRun.domain == domain)

    runs = list(db.execute(query.limit(limit)).scalars().all())
    return [
        EvaluationRunResponse(
            id=r.id,
            domain=r.domain,
            scenario_run_id=r.scenario_run_id,
            detector_version=r.detector_version,
            baseline_version=r.baseline_version,
            seed_type=r.seed_type,
            metrics=r.metrics,
            baseline_metrics=r.baseline_metrics,
            confusion_matrix=r.confusion_matrix,
            baseline_confusion_matrix=r.baseline_confusion_matrix,
            created_at=r.created_at,
        )
        for r in runs
    ]

