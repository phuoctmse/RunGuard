"""Tests for Pydantic models — validation and serialization."""

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from runguard.backend.models.runbook import Runbook
from runguard.backend.models.policy import Policy, AllowedAction, ForbiddenAction, PolicyScope
from runguard.backend.models.incident import Incident, IncidentSeverity, IncidentSource, IncidentStatus
from runguard.backend.models.audit import AuditRecord


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
