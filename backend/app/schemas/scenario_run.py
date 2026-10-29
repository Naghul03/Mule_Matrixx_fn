from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScenarioRunBase(BaseModel):
    domain: str = Field(default="current_money")
    scenario_identifier: str = Field(..., min_length=1, max_length=64)
    scenario_version: str = Field(default="1.0.0")
    generator_version: str = Field(default="1.0.0")
    seed: int = Field(..., description="Reproducibility seed")
    configuration_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="PENDING")


class ScenarioRunCreate(ScenarioRunBase):
    pass


class ScenarioRunRead(ScenarioRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

