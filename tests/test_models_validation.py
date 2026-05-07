"""Tests for Pydantic models — validation and serialization."""

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from runguard.backend.models.runbook import Runbook
from runguard.backend.models.policy import Policy, AllowedAction, ForbiddenAction, PolicyScope
from runguard.backend.models.incident import Incident, IncidentSeverity, IncidentSource, IncidentStatus
from runguard.backend.models.audit import AuditRecord
from runguard.backend.models.plan import (
    RemediationAction,
    RemediationPlan,
    ActionStatus,
    PolicyDecision,
    RootCause,
)


# === Runbook ===

def test_runbook_required_fields():
    """Should require id, title, scope."""
    with pytest.raises(ValidationError):
        Runbook()  # type: ignore


def test_runbook_defaults():
    """Should have correct default values."""
    r = Runbook(id="rb-1", title="Test", scope={})
    assert r.allowed_tools == []
    assert r.forbidden_tools == []
    assert r.severity == "medium"
    assert r.rollback_steps == []
    assert r.raw_markdown == ""
    assert r.version == 1


def test_runbook_serialization():
    """Should serialize to dict correctly."""
    r = Runbook(
        id="rb-1",
        title="Test",
        scope={"namespaces": ["default"]},
        allowed_tools=["rollout restart"],
        severity="high",
    )
    data = r.model_dump()
    assert data["id"] == "rb-1"
    assert data["title"] == "Test"
    assert data["scope"]["namespaces"] == ["default"]


def test_runbook_json_roundtrip():
    """Should survive JSON serialization roundtrip."""
    original = Runbook(
        id="rb-1",
        title="Test",
        scope={"ns": ["default"]},
        allowed_tools=["rollout restart"],
        severity="high",
        rollback_steps=["undo"],
    )
    json_str = original.model_dump_json()
    restored = Runbook.model_validate_json(json_str)
    assert restored.id == original.id
    assert restored.title == original.title
    assert restored.allowed_tools == original.allowed_tools


# === Policy ===

def test_policy_defaults():
    """Should have correct defaults."""
    p = Policy(id="pol-1", runbook_id="rb-1")
    assert p.allowed_actions == []
    assert p.forbidden_actions == []
    assert p.max_blast_radius_threshold == 0.3
    assert p.severity == "medium"
    assert p.scope.namespaces == []
    assert p.scope.workloads == []


def test_allowed_action_defaults():
    """Should have correct defaults."""
    a = AllowedAction(name="test")
    assert a.blast_radius == "low"
    assert a.requires_approval is False
    assert a.rollback_path == []


def test_forbidden_action_defaults():
    """Should have correct defaults."""
    f = ForbiddenAction(name="test")
    assert f.reason == ""


def test_policy_serialization():
    """Should serialize nested models correctly."""
    p = Policy(
        id="pol-1",
        runbook_id="rb-1",
        scope=PolicyScope(namespaces=["default"], workloads=["web-app"]),
        allowed_actions=[AllowedAction(name="rollout_restart", blast_radius="low")],
        forbidden_actions=[ForbiddenAction(name="delete", reason="blocked")],
        severity="high",
    )
    data = p.model_dump()
    assert data["allowed_actions"][0]["name"] == "rollout_restart"
    assert data["forbidden_actions"][0]["reason"] == "blocked"
    assert data["scope"]["namespaces"] == ["default"]
    assert data["scope"]["workloads"] == ["web-app"]
    assert data["severity"] == "high"


# === Incident ===

def test_incident_required_fields():
    """Should require all mandatory fields."""
    with pytest.raises(ValidationError):
        Incident()  # type: ignore


def test_incident_default_status():
    """Should default to PENDING status."""
    i = Incident(
        id="inc-1",
        source="manual",
        severity="high",
        environment="dev",
        namespace="default",
        workload="web-app",
        raw_alert="test",
    )
    assert i.status == IncidentStatus.PENDING


def test_incident_status_all_values():
    """All status values should be valid."""
    for status in IncidentStatus:
        i = Incident(
            id="inc-1",
            source="manual",
            severity="high",
            environment="dev",
            namespace="default",
            workload="web-app",
            raw_alert="test",
            status=status,
        )
        assert i.status == status


def test_incident_status_string_values():
    """Status enum values should be strings."""
    assert IncidentStatus.PENDING.value == "pending"
    assert IncidentStatus.ANALYZING.value == "analyzing"
    assert IncidentStatus.REQUIRES_APPROVAL.value == "requires_approval"
    assert IncidentStatus.EXECUTING.value == "executing"
    assert IncidentStatus.RESOLVED.value == "resolved"
    assert IncidentStatus.REJECTED.value == "rejected"
    assert IncidentStatus.FAILED.value == "failed"


def test_incident_timestamps_are_utc():
    """Timestamps should be UTC."""
    i = Incident(
        id="inc-1",
        source="manual",
        severity="high",
        environment="dev",
        namespace="default",
        workload="web-app",
        raw_alert="test",
    )
    assert i.created_at.tzinfo == timezone.utc
    assert i.updated_at.tzinfo == timezone.utc


def test_incident_serialization():
    """Should serialize correctly."""
    i = Incident(
        id="inc-1",
        source="prometheus",
        severity="high",
        environment="prod",
        namespace="default",
        workload="api",
        raw_alert="latency",
    )
    data = i.model_dump()
    assert data["id"] == "inc-1"
    assert data["status"] == "pending"
    assert "created_at" in data


def test_incident_severity_enum_values():
    """Severity enum should have all spec values."""
    assert IncidentSeverity.LOW == "low"
    assert IncidentSeverity.MEDIUM == "medium"
    assert IncidentSeverity.HIGH == "high"
    assert IncidentSeverity.CRITICAL == "critical"


def test_incident_source_enum_values():
    """Source enum should have all spec values."""
    assert IncidentSource.PROMETHEUS == "prometheus"
    assert IncidentSource.CLOUDWATCH == "cloudwatch"
    assert IncidentSource.MANUAL == "manual"


# === AuditRecord ===

def test_audit_record_defaults():
    """Should have correct defaults."""
    r = AuditRecord(incident_id="inc-1", event_type="test")
    assert r.details == {}
    assert r.id == ""
    assert r.actor == "system"
    assert r.timestamp is not None


def test_audit_record_timestamp_utc():
    """Timestamp should be UTC."""
    r = AuditRecord(incident_id="inc-1", event_type="test")
    assert r.timestamp.tzinfo == timezone.utc


def test_audit_record_with_complex_details():
    """Should handle nested dict in details."""
    details = {
        "action": "rollout_restart",
        "target": "web-app",
        "metadata": {"namespace": "default", "replicas": 3},
        "tags": ["urgent", "database"],
    }
    r = AuditRecord(incident_id="inc-1", event_type="action_executed", details=details)
    assert r.details == details


def test_audit_record_json_roundtrip():
    """Should survive JSON roundtrip."""
    original = AuditRecord(
        incident_id="inc-1",
        event_type="plan_generated",
        details={"key": "value"},
        id="aud-test-123",
    )
    json_str = original.model_dump_json()
    restored = AuditRecord.model_validate_json(json_str)
    assert restored.incident_id == original.incident_id
    assert restored.event_type == original.event_type
    assert restored.details == original.details
    assert restored.id == original.id


# === Incident runbook_id / plan_id ===

def test_incident_runbook_id_optional():
    """runbook_id should default to None."""
    i = Incident(
        id="inc-1", source="prometheus", severity="high",
        environment="dev", namespace="default", workload="web-app",
        raw_alert="test",
    )
    assert i.runbook_id is None
    assert i.plan_id is None


def test_incident_with_runbook_id():
    """Should accept runbook_id."""
    i = Incident(
        id="inc-1", source="manual", severity="high",
        environment="dev", namespace="default", workload="web-app",
        raw_alert="test", runbook_id="rb-abc",
    )
    assert i.runbook_id == "rb-abc"


def test_incident_serialization_includes_runbook_id():
    """Serialized incident should include runbook_id and plan_id."""
    i = Incident(
        id="inc-1", source="manual", severity="high",
        environment="dev", namespace="default", workload="web-app",
        raw_alert="test", runbook_id="rb-abc", plan_id="plan-xyz",
    )
    data = i.model_dump()
    assert data["runbook_id"] == "rb-abc"
    assert data["plan_id"] == "plan-xyz"


# === RemediationPlan ===

def test_remediation_plan_defaults():
    """Should have correct defaults."""
    p = RemediationPlan(id="plan-1", incident_id="inc-1")
    assert p.actions == []
    assert p.summary == ""
    assert p.root_causes == []


def test_remediation_plan_with_actions():
    """Should hold a list of RemediationAction."""
    action = RemediationAction(
        id="act-1", plan_id="plan-1", name="rollout_restart",
        target="web-app",
    )
    p = RemediationPlan(
        id="plan-1", incident_id="inc-1",
        summary="Restart pods", actions=[action],
    )
    assert len(p.actions) == 1
    assert p.actions[0].name == "rollout_restart"


def test_remediation_plan_json_roundtrip():
    """Should survive JSON roundtrip."""
    original = RemediationPlan(
        id="plan-1", incident_id="inc-1",
        summary="Fix OOM", root_causes=[
            RootCause(cause="OOM", confidence=0.9, evidence=["log"]),
        ],
    )
    json_str = original.model_dump_json()
    restored = RemediationPlan.model_validate_json(json_str)
    assert restored.id == original.id
    assert restored.root_causes[0].confidence == 0.9


# === RemediationAction ===

def test_remediation_action_defaults():
    """Should have correct defaults."""
    a = RemediationAction(id="act-1", plan_id="plan-1", name="rollout_restart", target="web-app")
    assert a.namespace == "default"
    assert a.parameters == {}
    assert a.blast_radius == "low"
    assert a.rollback_path == ""
    assert a.status == ActionStatus.PENDING
    assert a.policy_decision == PolicyDecision.REQUIRES_APPROVAL
    assert a.executed_at is None


def test_remediation_action_status_enum():
    """All status values should be valid."""
    for status in ActionStatus:
        a = RemediationAction(
            id="act-1", plan_id="plan-1", name="test", target="t", status=status,
        )
        assert a.status == status


def test_remediation_action_policy_decision_enum():
    """All policy decision values should be valid."""
    for decision in PolicyDecision:
        a = RemediationAction(
            id="act-1", plan_id="plan-1", name="test", target="t",
            policy_decision=decision,
        )
        assert a.policy_decision == decision


def test_remediation_action_json_roundtrip():
    """Should survive JSON roundtrip."""
    original = RemediationAction(
        id="act-1", plan_id="plan-1", name="scale_replicas",
        target="api", namespace="prod", parameters={"replicas": 3},
        blast_radius="medium", rollback_path="scale to 1",
    )
    json_str = original.model_dump_json()
    restored = RemediationAction.model_validate_json(json_str)
    assert restored.id == original.id
    assert restored.parameters == {"replicas": 3}
    assert restored.blast_radius == "medium"


# === RootCause ===

def test_root_cause_defaults():
    """Should have correct defaults."""
    r = RootCause(cause="OOM")
    assert r.confidence == 0.0
    assert r.evidence == []


def test_root_cause_with_data():
    """Should hold cause, confidence, evidence."""
    r = RootCause(
        cause="Memory limit too low",
        confidence=0.95,
        evidence=["OOMKilled in pod logs", "memory at 98%"],
    )
    assert r.confidence == 0.95
    assert len(r.evidence) == 2
