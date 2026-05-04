"""JSON file-based audit store."""

import json
import os
import uuid

from runguard.backend.models.audit import AuditRecord


class AuditStore:
    """Persists audit records as JSON files."""

    def __init__(self, store_path: str = "./data/audit"):
        self.store_path = store_path
        os.makedirs(store_path, exist_ok=True)

    def write(self, record: AuditRecord) -> str:
        """Write an audit record. Returns the record ID."""
        if not record.id:
            record.id = f"aud-{uuid.uuid4().hex[:12]}"

        incident_dir = os.path.join(self.store_path, record.incident_id)
        os.makedirs(incident_dir, exist_ok=True)

        ts = record.timestamp.isoformat().replace(":", "-")
        filename = f"{ts}_{record.id}.json"
        filepath = os.path.join(incident_dir, filename)

        with open(filepath, "w") as f:
            f.write(record.model_dump_json())

        return record.id

    def read(self, incident_id: str) -> list[AuditRecord]:
        """Read all audit records for an incident in chronological order."""
        incident_dir = os.path.join(self.store_path, incident_id)
        if not os.path.exists(incident_dir):
            return []

        records = []
        for filename in sorted(os.listdir(incident_dir)):
            if filename.endswith(".json"):
                filepath = os.path.join(incident_dir, filename)
                with open(filepath) as f:
                    data = json.load(f)
                    records.append(AuditRecord(**data))
        return records
