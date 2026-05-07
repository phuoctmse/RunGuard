"""Incident API routes."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runguard.backend.ai.reasoner import AIReasoner
from runguard.backend.audit.store import AuditStore
from runguard.backend.config import settings
from runguard.backend.executor.actions import execute_action
from runguard.backend.models.audit import AuditEventType, AuditRecord
from runguard.backend.notifications.slack import SlackNotifier

router = APIRouter(prefix="/incidents", tags=["incidents"])

# In-memory store for MVP (replace with DynamoDB later)
_incidents: dict[str, dict[str, Any]] = {}
_plans: dict[str, dict[str, Any]] = {}
_audit_store = AuditStore()
_ai_reasoner: AIReasoner | None = None


def _get_reasoner() -> AIReasoner:
    global _ai_reasoner
    if _ai_reasoner is None:
        _ai_reasoner = AIReasoner()
    return _ai_reasoner


_slack: SlackNotifier | None = None


def _get_slack() -> SlackNotifier | None:
    global _slack
    if _slack is None and settings.slack_webhook_url:
        _slack = SlackNotifier(webhook_url=settings.slack_webhook_url)
    return _slack


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


@router.post("/{incident_id}/analyze")
async def analyze_incident(incident_id: str) -> dict[str, Any]:
    """Analyze incident using Claude AI and generate remediation plan."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = _incidents[incident_id]
    valid_states = ("pending", "analyzing")
    if incident["status"] not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Incident {incident_id} not in analyzable state "
                f"(current: {incident['status']}, need: {', '.join(valid_states)})"
            ),
        )

    if incident_id in _plans and _plans[incident_id].get("actions"):
        raise HTTPException(
            status_code=400,
            detail=f"Incident {incident_id} already has a remediation plan",
        )

    incident["status"] = "analyzing"

    reasoner = _get_reasoner()
    ai_result = await reasoner.analyze(
        incident_id=incident_id,
        namespace=incident["namespace"],
        workload=incident["workload"],
        severity=incident["severity"],
        raw_alert=incident["raw_alert"],
        evidence={},
        runbook_title="",
    )

    if not ai_result.get("summary"):
        incident["status"] = "analyzing"
        _audit_store.write(
            AuditRecord(
                incident_id=incident_id,
                event_type=AuditEventType.ANALYSIS_FAILED,
                details={"error": "AI returned empty result"},
            )
        )
        raise HTTPException(status_code=500, detail="AI analysis failed -- retry")

    plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    actions: list[dict[str, Any]] = []

    for ai_action in ai_result.get("actions", []):
        action_id = f"act-{uuid.uuid4().hex[:8]}"
        action_name = ai_action.get("name", "unknown")

        action = {
            "id": action_id,
            "plan_id": plan_id,
            "name": action_name,
            "target": ai_action.get("target", ""),
            "namespace": incident["namespace"],
            "parameters": ai_action.get("parameters", {}),
            "blast_radius": "low",
            "rollback_path": "",
            "status": "pending",
            "policy_decision": "requires_approval",
            "policy_reason": "Default: requires approval",
        }
        actions.append(action)

    plan = {
        "id": plan_id,
        "incident_id": incident_id,
        "actions": actions,
        "summary": ai_result.get("summary", ""),
        "root_causes": ai_result.get("root_causes", []),
    }
    _plans[incident_id] = plan
    incident["plan_id"] = plan_id

    _audit_store.write(
        AuditRecord(
            incident_id=incident_id,
            event_type=AuditEventType.PLAN_GENERATED,
            details={"plan_id": plan_id, "action_count": len(actions)},
        )
    )

    requires_approval = any(
        a["policy_decision"] == "requires_approval" for a in actions
    )
    if requires_approval:
        incident["status"] = "requires_approval"
    else:
        incident["status"] = "resolved"

    return {
        "incident_id": incident_id,
        "status": incident["status"],
        "plan": plan,
    }


@router.post("/{incident_id}/execute")
async def execute_incident(incident_id: str) -> dict[str, Any]:
    """Execute approved remediation actions for an incident."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = _incidents[incident_id]
    if incident["status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Incident {incident_id} not in approved state "
                f"(current: {incident['status']})"
            ),
        )

    plan = _plans.get(incident_id)
    if not plan or not plan.get("actions"):
        raise HTTPException(
            status_code=400,
            detail=f"No plan found for incident {incident_id}",
        )

    incident["status"] = "executing"
    _audit_store.write(
        AuditRecord(
            incident_id=incident_id,
            event_type=AuditEventType.EXECUTION_STARTED,
        )
    )

    slack = _get_slack()
    results: list[dict[str, Any]] = []
    has_failure = False

    for action in plan["actions"]:
        if action.get("policy_decision") == "blocked":
            continue
        if action.get("status") not in ("approved",):
            continue

        result = execute_action(
            action_name=action["name"],
            target=action["target"],
            namespace=action.get("namespace", "default"),
            parameters=action.get("parameters", {}),
        )
        results.append(
            {
                "action_id": action["id"],
                "name": action["name"],
                "status": result["status"],
                "output": result.get("output", ""),
                "error": result.get("error", ""),
            }
        )

        if result["status"] == "completed":
            action["status"] = "completed"
            _audit_store.write(
                AuditRecord(
                    incident_id=incident_id,
                    event_type=AuditEventType.ACTION_EXECUTED,
                    details={"action_id": action["id"], "name": action["name"]},
                )
            )
            if slack:
                try:
                    await slack.send_action_executed(incident_id, action["name"])
                except Exception:
                    pass  # fire-and-forget
        else:
            action["status"] = "failed"
            has_failure = True
            _audit_store.write(
                AuditRecord(
                    incident_id=incident_id,
                    event_type=AuditEventType.ACTION_FAILED,
                    details={
                        "action_id": action["id"],
                        "name": action["name"],
                        "error": result.get("error", ""),
                    },
                )
            )
            if slack:
                try:
                    await slack.send_action_failed(
                        incident_id, action["name"], result.get("error", "")
                    )
                except Exception:
                    pass  # fire-and-forget

    incident["status"] = "failed" if has_failure else "resolved"

    if not has_failure and slack:
        try:
            await slack.send_resolved(
                incident_id, plan.get("summary", "All actions completed")
            )
        except Exception:
            pass  # fire-and-forget

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=207 if has_failure else 200,
        content={
            "incident_id": incident_id,
            "status": incident["status"],
            "results": results,
        },
    )
