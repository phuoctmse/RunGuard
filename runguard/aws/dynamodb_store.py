"""DynamoDB audit store — persistent audit records with TTL."""

import boto3
from boto3.dynamodb.conditions import Key

from runguard.backend.models.audit import AuditRecord


class DynamoDBAuditStore:
    """Persists audit records in DynamoDB."""

    def __init__(
        self, table_name: str = "runguard-audit", region_name: str = "us-east-1"
    ):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def write(self, record: AuditRecord) -> str:
        item = {
            "incident_id": record.incident_id,
            "timestamp": record.timestamp.isoformat(),
            "event_type": record.event_type,
            "details": record.details,
            "id": record.id,
        }
        self.table.put_item(Item=item)
        return record.id

    def read(self, incident_id: str) -> list[AuditRecord]:
        response = self.table.query(
            KeyConditionExpression=Key("incident_id").eq(incident_id),
            ScanIndexForward=True,
        )
        return [
            AuditRecord(
                incident_id=item["incident_id"],
                event_type=item["event_type"],
                details=item.get("details", {}),
                id=item.get("id", ""),
            )
            for item in response.get("Items", [])
        ]
