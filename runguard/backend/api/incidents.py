"""Incident API routes."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/incidents", tags=["incidents"])

# In-memory store for MVP (replace with DynamoDB later)
_incidents: dict[str, dict[str, Any]] = {}
_plans: dict[str, dict[str, Any]] = {}


class IncidentCreateRequest(BaseModel):
    source: str
    severity: str
    environment: str
    namespace: str
    workload: str
    raw_alert: str
    runbook_id: str | None = None  # required for manual incidents


@router.post("", status_code=201)
async def create_incident(request: IncidentCreateRequest) -> dict[str, Any]:
    """Create a new incident from alert or manual input."""
    if request.source == "manual" and not request.runbook_id:
        raise HTTPException(
            status_code=400,
            detail="Manual incidents require runbook_id",
        )
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    incident = {
        "id": incident_id,
        "source": request.source,
        "severity": request.severity,
        "environment": request.environment,
        "namespace": request.namespace,
        "workload": request.workload,
        "raw_alert": request.raw_alert,
        "runbook_id": request.runbook_id,
        "plan_id": None,
        "status": "pending",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _incidents[incident_id] = incident
    return incident


@router.get("")
async def list_incidents() -> list[dict[str, Any]]:
    """List all incidents."""
    return list(_incidents.values())


@router.get("/{incident_id}")
async def get_incident(incident_id: str) -> dict[str, Any]:
    """Get incident details by ID."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incidents[incident_id]


@router.get("/{incident_id}/plan")
async def get_incident_plan(incident_id: str) -> dict[str, Any]:
    """Get remediation plan for an incident."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _plans.get(incident_id, {})
