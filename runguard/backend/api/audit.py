"""Audit API routes."""

from typing import Any

from fastapi import APIRouter

from runguard.backend.audit.store import AuditStore

router = APIRouter(prefix="/audit", tags=["audit"])

_store = AuditStore()


@router.get("/{incident_id}")
async def get_audit_records(incident_id: str) -> list[dict[str, Any]]:
    """Get all audit records for an incident."""
    records = _store.read(incident_id)
    return [r.model_dump() for r in records]
