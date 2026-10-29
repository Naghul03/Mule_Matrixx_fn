from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EvaluationRunRequest(BaseModel):
    scenario_run_id: str
    seed_type: str = Field(default="HOLDOUT")  # DEVELOPMENT, VALIDATION, HOLDOUT
    domain: str = Field(default="current_money")


class EvaluationRunResponse(BaseModel):
    id: str
    domain: str
    scenario_run_id: str
    detector_version: str
    baseline_version: str
    seed_type: str
    metrics: Dict[str, Any]
    baseline_metrics: Dict[str, Any]
    confusion_matrix: Optional[Dict[str, Any]] = None
    baseline_confusion_matrix: Optional[Dict[str, Any]] = None
    created_at: datetime

