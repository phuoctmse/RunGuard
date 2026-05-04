"""Audit record data model."""

from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AuditRecord(BaseModel):
    """An immutable audit record for an incident event."""

    incident_id: str
    event_type: str
    details: dict = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = ""
