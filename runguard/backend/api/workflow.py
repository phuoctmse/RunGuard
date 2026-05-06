"""Workflow API routes — approve/reject actions."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runguard.backend.workflow.approval import ApprovalWorkflow

router = APIRouter(prefix="/incidents", tags=["workflow"])

_workflow: ApprovalWorkflow | None = None


class ApproveRequest(BaseModel):
    approver: str = "dashboard-user"


class RejectRequest(BaseModel):
    rejector: str = "dashboard-user"
    reason: str = ""


@router.post("/{incident_id}/approve")
async def approve_action(
    incident_id: str, request: ApproveRequest | None = None
) -> dict[str, Any]:
    if not _workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    approver = request.approver if request else "dashboard-user"
    request_id = _workflow.get_or_create_request(incident_id)
    result = _workflow.approve(request_id, approver)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve — action may be expired or already processed",
        )
    return {"status": "approved", "incident_id": incident_id}


@router.post("/{incident_id}/reject")
async def reject_action(
    incident_id: str, request: RejectRequest | None = None
) -> dict[str, Any]:
    if not _workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    rejector = request.rejector if request else "dashboard-user"
    reason = request.reason if request else ""
    request_id = _workflow.get_or_create_request(incident_id)
    result = _workflow.reject(request_id, rejector, reason)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot reject — action may be expired or already processed",
        )
    return {"status": "rejected", "incident_id": incident_id}
