"""Workflow API routes — approve/reject actions."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/incidents", tags=["workflow"])

_workflow = None


class ApproveRequest(BaseModel):
    approver: str


class RejectRequest(BaseModel):
    rejector: str
    reason: str = ""


@router.post("/{incident_id}/approve")
async def approve_action(incident_id: str, request: ApproveRequest):
    if not _workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    request_id = _workflow.get_or_create_request(incident_id)
    result = _workflow.approve(request_id, request.approver)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve — action may be expired or already processed",
        )
    return {"status": "approved", "incident_id": incident_id}


@router.post("/{incident_id}/reject")
async def reject_action(incident_id: str, request: RejectRequest):
    if not _workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    request_id = _workflow.get_or_create_request(incident_id)
    result = _workflow.reject(request_id, request.rejector, request.reason)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot reject — action may be expired or already processed",
        )
    return {"status": "rejected", "incident_id": incident_id}
