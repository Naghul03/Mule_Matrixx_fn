from typing import Any, Dict, List
from pydantic import BaseModel


class DashboardMetricsResponse(BaseModel):
    domain: str
    total_cases: int
    open_cases: int
    escalated_cases: int
    high_risk_alerts: int
    medium_risk_alerts: int
    low_risk_alerts: int
    total_transactions: int
    total_volume: float
    recent_scenario_runs: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]

