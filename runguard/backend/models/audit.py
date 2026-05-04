"""Audit record data model."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    """An immutable audit record for an incident event."""

    incident_id: str
    event_type: str
    details: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id: str = ""
