"""Incident data model."""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class IncidentStatus(str, Enum):
    """Incident lifecycle status."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    REQUIRES_APPROVAL = "requires_approval"
    EXECUTING = "executing"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    FAILED = "failed"


class Incident(BaseModel):
    """An incident record created from an alert or manual input."""

    id: str
    source: str  # prometheus, cloudwatch, manual
    severity: str
    environment: str
    namespace: str
    workload: str
    raw_alert: str
    status: IncidentStatus = IncidentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
