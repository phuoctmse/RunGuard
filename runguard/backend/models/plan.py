"""Remediation plan and action data models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ActionStatus(StrEnum):
    """Lifecycle status of a remediation action."""

    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class PolicyDecision(StrEnum):
    """Decision from the policy engine."""

    APPROVED = "approved"
    REQUIRES_APPROVAL = "requires_approval"
    BLOCKED = "blocked"


class RootCause(BaseModel):
    """A root cause identified by AI analysis."""

    cause: str
    confidence: float = 0.0
    evidence: list[str] = []


class RemediationAction(BaseModel):
    """A single remediation action within a plan."""

    id: str
    plan_id: str
    name: str  # tool name from Allowed Tools
    target: str  # deployment/pod name
    namespace: str = "default"
    parameters: dict[str, Any] = {}  # action-specific params
    blast_radius: str = "low"  # low, medium, high
    rollback_path: str = ""
    status: ActionStatus = ActionStatus.PENDING
    policy_decision: PolicyDecision = PolicyDecision.REQUIRES_APPROVAL
    policy_reason: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    executed_at: datetime | None = None


class RemediationPlan(BaseModel):
    """A remediation plan containing actions to resolve an incident."""

    id: str
    incident_id: str
    actions: list[RemediationAction] = []
    summary: str = ""
    root_causes: list[RootCause] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
