"""Extract structured metadata from parsed runbook sections."""

import uuid
from runguard.backend.models.runbook import Runbook


def extract_metadata(sections: dict, raw_markdown: str = "") -> Runbook:
    """Convert parsed sections into a Runbook model."""
    runbook_id = f"rb-{uuid.uuid4().hex[:8]}"

    scope = sections.get("scope", {})
    if isinstance(scope, list):
        scope = {"namespaces": [], "workloads": []}

    return Runbook(
        id=runbook_id,
        title=sections.get("title", "Untitled Runbook"),
        scope=scope,
        allowed_tools=sections.get("allowed_tools", []),
        forbidden_tools=sections.get("forbidden_tools", []),
        severity=sections.get("severity", "medium"),
        rollback_steps=sections.get("rollback_steps", []),
        raw_markdown=raw_markdown,
    )
