"""Webhook API routes for receiving external alerts."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from runguard.backend.api.incidents import _incidents
from runguard.backend.config import settings
from runguard.backend.webhooks.alertmanager import AlertmanagerParser

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_alertmanager_parser = AlertmanagerParser()
_security = HTTPBearer()


def _verify_webhook_token(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> str:
    """Verify Bearer token against configured webhook secret."""
    if not settings.webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    if credentials.credentials != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook token")
    return credentials.credentials


@router.post("/alertmanager")
async def receive_alertmanager(
    request: Request,
    _token: str = Depends(_verify_webhook_token),
) -> dict[str, Any]:
    """Receive Alertmanager webhook and create incidents."""
    payload = await request.json()
    parsed = _alertmanager_parser.parse(payload)

    incident_ids: list[str] = []
    for inc_data in parsed:
        incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        incident = {
            "id": incident_id,
            "source": inc_data["source"],
            "severity": inc_data["severity"],
            "environment": "production",
            "namespace": inc_data["namespace"],
            "workload": inc_data["workload"],
            "raw_alert": inc_data["raw_alert"],
            "runbook_id": None,
            "plan_id": None,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        _incidents[incident_id] = incident
        incident_ids.append(incident_id)

    return {
        "incidents_created": len(incident_ids),
        "incident_ids": incident_ids,
    }
