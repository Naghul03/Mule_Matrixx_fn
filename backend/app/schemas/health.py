from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Service status")
    service: str = Field("mule-matrix-backend", description="Service identifier")
    version: str = Field("0.1.0", description="API version")
    environment: str = Field(..., description="Active environment name")


class DatabaseHealthResponse(BaseModel):
    status: str = Field(..., description="Database connection status: 'connected' or 'disconnected'")
    database: str = Field(..., description="Target database name")
    latency_ms: Optional[float] = Field(None, description="Round-trip ping latency in milliseconds")
    error: Optional[str] = Field(None, description="Sanitized connection error description")

