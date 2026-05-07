"""Workflow API routes — approve/reject actions."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runguard.backend.api.incidents import _incidents, _plans
from runguard.backend.workflow.approval import ApprovalWorkflow

router = APIRouter(prefix="/incidents", tags=["workflow"])

_workflow: ApprovalWorkflow | None = None


class ApproveRequest(BaseModel):
    approver: str = "dashboard-user"


class RejectRequest(BaseModel):
    rejector: str = "dashboard-user"
    reason: str = ""


def _validate_incident_state(incident_id: str) -> dict[str, Any]:
    """Check that incident exists and is in requires_approval state."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident = _incidents[incident_id]
    if incident["status"] != "requires_approval":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Incident {incident_id} is not in requires_approval state "
                f"(current: {incident['status']})"
            ),
        )
    return incident


def _approve_actions(incident_id: str) -> str:
    """Approve actions in the incident's plan, skipping blocked ones.

    Returns the new incident status: "approved" or "failed".
    """
    plan = _plans.get(incident_id)
    if not plan or not plan.get("actions"):
        return "approved"

    actions = plan["actions"]
    approved_count = 0
    blocked_count = 0

    for action in actions:
        if action.get("policy_decision") == "blocked":
            blocked_count += 1
            continue
        if (
            action.get("status") == "pending"
            and action.get("policy_decision") == "requires_approval"
        ):
            action["status"] = "approved"
            approved_count += 1

    # All actions blocked → incident fails
    if approved_count == 0 and blocked_count == len(actions):
        return "failed"

    return "approved"


def _check_all_approved(incident_id: str) -> bool:
    """Check if all requires_approval actions are now approved."""
    plan = _plans.get(incident_id)
    if not plan or not plan.get("actions"):
        return False

    for action in plan["actions"]:
        if action.get("policy_decision") == "requires_approval" and action.get("status") != "approved":
            return False
    return True


@router.post("/{incident_id}/approve")
async def approve_action(
    incident_id: str, request: ApproveRequest | None = None
) -> dict[str, Any]:
    if not _workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    _validate_incident_state(incident_id)
    approver = request.approver if request else "dashboard-user"
    request_id = _workflow.get_or_create_request(incident_id)
    result = _workflow.approve(request_id, approver)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve — action may be expired or already processed",
        )
    new_status = _approve_actions(incident_id)
    _incidents[incident_id]["status"] = new_status
    return {"status": new_status, "incident_id": incident_id}


@router.post("/{incident_id}/actions/{action_id}/approve")
async def approve_single_action(
    incident_id: str, action_id: str, request: ApproveRequest | None = None
) -> dict[str, Any]:
    """Approve a single action in the incident's plan."""
    _validate_incident_state(incident_id)

    plan = _plans.get(incident_id)
    if not plan or not plan.get("actions"):
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found in incident plan")

    target_action = None
    for action in plan["actions"]:
        if action.get("id") == action_id:
            target_action = action
            break

    if target_action is None:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found in incident plan")

    if target_action.get("policy_decision") == "blocked":
        raise HTTPException(
            status_code=400,
            detail=f"Action {action_id} is blocked by policy: {target_action.get('policy_reason', 'unknown')}",
        )

    if target_action.get("status") == "approved":
        return {"status": "already_approved", "action_id": action_id, "incident_id": incident_id}

    approver = request.approver if request else "dashboard-user"
    target_action["status"] = "approved"

    # Check if all requires_approval actions are now approved → auto-transition
    if _check_all_approved(incident_id):
        _incidents[incident_id]["status"] = "approved"

    return {"status": "approved", "action_id": action_id, "incident_id": incident_id}


@router.post("/{incident_id}/reject")
async def reject_action(
    incident_id: str, request: RejectRequest | None = None
) -> dict[str, Any]:
    if not _workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")
    _validate_incident_state(incident_id)
    rejector = request.rejector if request else "dashboard-user"
    reason = request.reason if request else ""
    request_id = _workflow.get_or_create_request(incident_id)
    result = _workflow.reject(request_id, rejector, reason)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot reject — action may be expired or already processed",
        )
    _incidents[incident_id]["status"] = "rejected"
    return {"status": "rejected", "incident_id": incident_id}
