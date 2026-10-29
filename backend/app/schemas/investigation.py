from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class CytoscapeGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class KingpinRankingItem(BaseModel):
    rank: int
    accountId: str
    accountRef: str
    alias: str
    riskScore: float
    kingpinScore: float
    totalReceived: float
    totalDisbursed: float
    inboundTransfers: int
    outboundTransfers: int
    betweennessCentrality: float
    rationale: str


class MuleRankingItem(BaseModel):
    rank: int
    accountId: str
    accountRef: str
    alias: str
    riskScore: float
    muleScore: float
    passThroughRatio: float
    totalReceived: float
    totalDisbursed: float
    rationale: str


class RankingsResponse(BaseModel):
    kingpins: List[KingpinRankingItem]
    mules: List[MuleRankingItem]


class FIFOAttributionItem(BaseModel):
    transactionId: str
    transactionRef: str
    amount: float
    timestamp: str
    consumedAllocations: List[Dict[str, Any]]
    unattributedAmount: float
    isDirectAttribution: bool

