"""Incident data model."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IncidentStatus(StrEnum):
    """Incident lifecycle status."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    REQUIRES_APPROVAL = "requires_approval"
    EXECUTING = "executing"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    FAILED = "failed"


class IncidentSeverity(StrEnum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentSource(StrEnum):
    """Sources that can create incidents."""

    PROMETHEUS = "prometheus"
    CLOUDWATCH = "cloudwatch"
    MANUAL = "manual"


class Incident(BaseModel):
    """An incident record created from an alert or manual input."""

    id: str
    source: str  # prometheus, cloudwatch, manual
    severity: str  # low, medium, high, critical
    environment: str
    namespace: str
    workload: str
    raw_alert: str
    status: IncidentStatus = IncidentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
