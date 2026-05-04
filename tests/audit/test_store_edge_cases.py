"""Tests for audit store — edge cases."""

import json
import os
import tempfile
import pytest
from runguard.backend.audit.store import AuditStore
from runguard.backend.models.audit import AuditRecord


@pytest.fixture
def audit_store():
    """Create a temporary audit store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = AuditStore(store_path=tmpdir)
        yield store


def test_write_preserves_existing_id(audit_store):
    """Should not overwrite ID if already set."""
    record = AuditRecord(
        incident_id="inc-001",
        event_type="test",
        details={},
        id="custom-id-123",
    )
    result_id = audit_store.write(record)
    assert result_id == "custom-id-123"


def test_write_generates_id_with_prefix(audit_store):
    """Should generate ID with aud- prefix."""
    record = AuditRecord(incident_id="inc-001", event_type="test", details={})
    record_id = audit_store.write(record)
    assert record_id.startswith("aud-")


def test_write_creates_directory_structure(audit_store):
    """Should create incident directory."""
    record = AuditRecord(incident_id="inc-001", event_type="test", details={})
    audit_store.write(record)

    incident_dir = os.path.join(audit_store.store_path, "inc-001")
    assert os.path.exists(incident_dir)


def test_write_creates_json_file(audit_store):
    """Should create a JSON file with record data."""
    record = AuditRecord(
        incident_id="inc-001",
        event_type="incident_created",
        details={"source": "manual"},
    )
    audit_store.write(record)

    incident_dir = os.path.join(audit_store.store_path, "inc-001")
    files = os.listdir(incident_dir)
    assert len(files) == 1
    assert files[0].endswith(".json")

    with open(os.path.join(incident_dir, files[0])) as f:
        data = json.load(f)
    assert data["incident_id"] == "inc-001"
    assert data["event_type"] == "incident_created"


def test_write_multiple_records_same_incident(audit_store):
    """Should create separate files for each record."""
    for i in range(5):
        record = AuditRecord(incident_id="inc-001", event_type=f"event-{i}", details={})
        audit_store.write(record)

    incident_dir = os.path.join(audit_store.store_path, "inc-001")
    files = os.listdir(incident_dir)
    assert len(files) == 5


def test_write_different_incidents_separate_dirs(audit_store):
    """Should create separate directories for different incidents."""
    audit_store.write(AuditRecord(incident_id="inc-001", event_type="test", details={}))
    audit_store.write(AuditRecord(incident_id="inc-002", event_type="test", details={}))

    assert os.path.exists(os.path.join(audit_store.store_path, "inc-001"))
    assert os.path.exists(os.path.join(audit_store.store_path, "inc-002"))


def test_read_empty_incident(audit_store):
    """Should return empty list for non-existent incident."""
    assert audit_store.read("inc-nonexistent") == []


def test_read_skips_non_json_files(audit_store):
    """Should ignore non-JSON files in incident directory."""
    incident_dir = os.path.join(audit_store.store_path, "inc-001")
    os.makedirs(incident_dir)

    # Create a non-JSON file
    with open(os.path.join(incident_dir, "notes.txt"), "w") as f:
        f.write("not json")

    # Create a valid JSON file
    record = AuditRecord(incident_id="inc-001", event_type="test", details={})
    audit_store.write(record)

    records = audit_store.read("inc-001")
    assert len(records) == 1


def test_read_preserves_details(audit_store):
    """Should preserve complex details dict."""
    details = {
        "source": "prometheus",
        "severity": "high",
        "tags": ["crash", "database"],
        "nested": {"key": "value"},
    }
    record = AuditRecord(incident_id="inc-001", event_type="test", details=details)
    audit_store.write(record)

    records = audit_store.read("inc-001")
    assert records[0].details == details


def test_write_read_roundtrip(audit_store):
    """Should survive full write -> read roundtrip."""
    original = AuditRecord(
        incident_id="inc-001",
        event_type="plan_generated",
        details={"actions": ["rollout_restart"]},
    )
    audit_store.write(original)

    records = audit_store.read("inc-001")
    restored = records[0]

    assert restored.incident_id == original.incident_id
    assert restored.event_type == original.event_type
    assert restored.details == original.details
    assert restored.id == original.id
