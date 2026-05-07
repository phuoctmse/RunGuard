"""JSON file-based audit store."""

import json
import os
import re
import uuid

from runguard.backend.models.audit import AuditRecord

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


def _validate_incident_id(incident_id: str) -> str:
    """Validate incident_id to prevent path traversal."""
    if not _SAFE_ID_RE.match(incident_id):
        raise ValueError(f"Invalid incident_id: {incident_id!r}")
    return incident_id


class AuditStore:
    """Persists audit records as JSON files."""

    def __init__(self, store_path: str = "./data/audit"):
        self.store_path = store_path
        os.makedirs(store_path, exist_ok=True)

    def write(self, record: AuditRecord) -> str:
        """Write an audit record. Returns the record ID."""
        _validate_incident_id(record.incident_id)

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
        _validate_incident_id(incident_id)

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
