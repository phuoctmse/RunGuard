"""Tests for data models."""

from runguard.backend.models.runbook import Runbook
from runguard.backend.models.policy import Policy, AllowedAction, ForbiddenAction
from runguard.backend.models.incident import Incident, IncidentStatus
from runguard.backend.models.audit import AuditRecord


def test_runbook_creation():
    runbook = Runbook(
        id="rb-001",
        title="Pod CrashLoop",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["rollout restart", "scale deployment"],
        forbidden_tools=["delete deployment"],
        severity="medium",
        rollback_steps=["kubectl rollout undo deployment/{name} -n {namespace}"],
    )
    assert runbook.id == "rb-001"
    assert runbook.severity == "medium"
    assert len(runbook.allowed_tools) == 2


def test_policy_creation():
    policy = Policy(
        id="pol-001",
        runbook_id="rb-001",
        allowed_actions=[
            AllowedAction(name="rollout_restart", blast_radius="low", requires_approval=False),
        ],
        forbidden_actions=[
            ForbiddenAction(name="delete_deployment", reason="forbidden by runbook"),
        ],
        max_blast_radius_threshold=0.3,
    )
    assert policy.runbook_id == "rb-001"
    assert len(policy.allowed_actions) == 1
    assert policy.allowed_actions[0].requires_approval is False


def test_incident_creation():
    incident = Incident(
        id="inc-001",
        source="manual",
        severity="high",
        environment="dev",
        namespace="default",
        workload="web-app",
        raw_alert="Pod CrashLoopBackOff detected",
    )
    assert incident.status == IncidentStatus.PENDING
    assert incident.id == "inc-001"


def test_incident_status_lifecycle():
    incident = Incident(
        id="inc-002",
        source="prometheus",
        severity="medium",
        environment="dev",
        namespace="default",
        workload="api-server",
        raw_alert="High latency detected",
    )
    assert incident.status == IncidentStatus.PENDING
    incident.status = IncidentStatus.ANALYZING
    assert incident.status == IncidentStatus.ANALYZING


def test_audit_record_creation():
    record = AuditRecord(
        incident_id="inc-001",
        event_type="incident_created",
        details={"source": "manual", "severity": "high"},
    )
    assert record.incident_id == "inc-001"
    assert record.event_type == "incident_created"
    assert record.timestamp is not None
