"""Pydantic models for cost tracking."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CostSource(StrEnum):
    """Source of cost data."""

    AWS_COST_EXPLORER = "aws_cost_explorer"
    OPENCOST = "opencost"
    ESTIMATED = "estimated"


class CostEntry(BaseModel):
    """A single cost data point."""

    source: CostSource
    amount: float
    currency: str = "USD"
    period_start: datetime
    period_end: datetime
    namespace: str = ""
    workload: str = ""
    incident_id: str = ""
    description: str = ""


class NamespaceCost(BaseModel):
    """Cost breakdown for a Kubernetes namespace."""

    namespace: str
    cpu_cost: float = 0.0
    memory_cost: float = 0.0
    storage_cost: float = 0.0
    total_cost: float = 0.0
    period_start: datetime
    period_end: datetime


class IncidentCostSummary(BaseModel):
    """Cost summary for an incident."""

    incident_id: str
    total_cost: float = 0.0
    currency: str = "USD"
    cost_entries: list[CostEntry] = Field(default_factory=list)
    namespace_costs: list[NamespaceCost] = Field(default_factory=list)
    estimated_action_cost: float = 0.0


class ActionCostEstimate(BaseModel):
    """Estimated cost impact of a proposed action."""

    action_name: str
    estimated_cost: float = 0.0
    currency: str = "USD"
    confidence: float = 0.5
    description: str = ""
