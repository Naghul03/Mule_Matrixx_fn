from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioRunRequest(BaseModel):
    scenario_id: str = Field(..., description="scenario_1, scenario_3, scenario_4, or scenario_2")
    seed: int = Field(default=42, description="PRNG seed for reproducible generation")
    base_amount: Optional[Decimal] = Field(None, gt=Decimal("0"), description="Optional primary monetary amount")
    num_attack_accounts: int = Field(default=5, ge=3, le=10, description="Attack-pattern account count (capped at 10)")
    num_decoys: int = Field(default=4, ge=0, le=20, description="Separate decoy background population size")
    custom_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ScenarioTemplate(BaseModel):
    id: str
    name: str
    domain: str
    description: str
    default_seed: int
    default_amount: Decimal
    key_typologies: List[str]


class ScenarioRunResponse(BaseModel):
    id: str
    domain: str
    scenario_identifier: str
    scenario_version: str
    generator_version: str
    seed: int
    status: str
    configuration_json: Dict[str, Any]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    transaction_count: Optional[int] = 0
    alert_count: Optional[int] = 0
    case_count: Optional[int] = 0

