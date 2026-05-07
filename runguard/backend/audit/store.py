"""JSON file-based audit store."""

import json
import uuid
from pathlib import Path

from runguard.backend.models.audit import AuditRecord


class AuditStore:
    """Persists audit records as JSON files."""

    def __init__(self, store_path: str = "./data/audit"):
        self.store_path = Path(store_path).resolve()
        self.store_path.mkdir(parents=True, exist_ok=True)

    def _safe_dir(self, incident_id: str) -> Path:
        """Resolve incident directory and verify it stays within store_path."""
        resolved = (self.store_path / incident_id).resolve()
        if not resolved.is_relative_to(self.store_path):
            raise ValueError(f"Path traversal detected: {incident_id!r}")
        return resolved

    def _safe_file(self, incident_id: str, filename: str) -> Path:
        """Resolve file path and verify it stays within store_path."""
        resolved = (self.store_path / incident_id / filename).resolve()
        if not resolved.is_relative_to(self.store_path):
            raise ValueError(f"Path traversal detected: {filename!r}")
        return resolved

    def write(self, record: AuditRecord) -> str:
        """Write an audit record. Returns the record ID."""
        if not record.id:
            record.id = f"aud-{uuid.uuid4().hex[:12]}"

        incident_dir = self._safe_dir(record.incident_id)
        incident_dir.mkdir(parents=True, exist_ok=True)

        ts = record.timestamp.isoformat().replace(":", "-")
        filename = f"{ts}_{record.id}.json"
        filepath = self._safe_file(record.incident_id, filename)

        filepath.write_text(record.model_dump_json())

        return record.id

    def read(self, incident_id: str) -> list[AuditRecord]:
        """Read all audit records for an incident in chronological order."""
        incident_dir = self._safe_dir(incident_id)
        if not incident_dir.exists():
            return []

        records = []
        for entry in sorted(incident_dir.iterdir()):
            if entry.suffix == ".json" and entry.is_file():
                filepath = self._safe_file(incident_id, entry.name)
                data = json.loads(filepath.read_text())
                records.append(AuditRecord(**data))
        return records
