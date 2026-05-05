"""Tests for DynamoDB audit store."""

import boto3
import pytest
from moto import mock_aws

from runguard.aws.dynamodb_store import DynamoDBAuditStore
from runguard.backend.models.audit import AuditRecord


@pytest.fixture
def dynamodb_store():
    with mock_aws():
        conn = boto3.resource("dynamodb", region_name="us-east-1")
        conn.create_table(
            TableName="runguard-audit",
            KeySchema=[
                {"AttributeName": "incident_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "incident_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield DynamoDBAuditStore(table_name="runguard-audit", region_name="us-east-1")


def test_write_record(dynamodb_store):
    record = AuditRecord(
        incident_id="inc-001",
        event_type="incident_created",
        details={"source": "manual"},
    )
    record_id = dynamodb_store.write(record)
    assert record_id is not None


def test_read_records(dynamodb_store):
    r1 = AuditRecord(incident_id="inc-001", event_type="created", details={})
    r2 = AuditRecord(incident_id="inc-001", event_type="plan_generated", details={})
    dynamodb_store.write(r1)
    dynamodb_store.write(r2)

    records = dynamodb_store.read("inc-001")
    assert len(records) == 2


def test_read_nonexistent(dynamodb_store):
    records = dynamodb_store.read("inc-999")
    assert records == []
