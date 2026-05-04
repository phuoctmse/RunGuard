"""Tests for file-based audit store."""

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


def test_write_record(audit_store):
    record = AuditRecord(
        incident_id="inc-001",
        event_type="incident_created",
        details={"source": "manual"},
    )
    audit_store.write(record)
    assert record.id != ""


def test_read_records(audit_store):
    record1 = AuditRecord(incident_id="inc-001", event_type="incident_created", details={})
    record2 = AuditRecord(incident_id="inc-001", event_type="plan_generated", details={})
    audit_store.write(record1)
    audit_store.write(record2)

    records = audit_store.read("inc-001")
    assert len(records) == 2
    assert records[0].event_type == "incident_created"


def test_read_returns_chronological_order(audit_store):
    record1 = AuditRecord(incident_id="inc-001", event_type="first", details={})
    record2 = AuditRecord(incident_id="inc-001", event_type="second", details={})
    audit_store.write(record1)
    audit_store.write(record2)

    records = audit_store.read("inc-001")
    assert records[0].event_type == "first"
    assert records[1].event_type == "second"


def test_read_nonexistent_returns_empty(audit_store):
    records = audit_store.read("inc-999")
    assert records == []
