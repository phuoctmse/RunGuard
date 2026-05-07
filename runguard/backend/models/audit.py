"""Audit record data model."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(StrEnum):
    """Types of audit events."""

    INCIDENT_CREATED = "incident_created"
    WEBHOOK_RECEIVED = "webhook_received"
    PLAN_GENERATED = "plan_generated"
    ANALYSIS_FAILED = "analysis_failed"
    ACTION_VALIDATED = "action_validated"
    ACTION_AUTO_APPROVED = "action_auto_approved"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTION_STARTED = "execution_started"
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"
    GITOPS_COMMIT = "gitops_commit"


class AuditRecord(BaseModel):
    """An immutable audit record for an incident event."""

    incident_id: str
    event_type: str
    actor: str = "system"
    details: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id: str = ""
