"""AI prompt templates for incident analysis."""

from typing import Any

SYSTEM_PROMPT = """\
You are an SRE incident analyst for Kubernetes workloads. \
Analyze incidents, identify root causes with confidence scores, \
and propose safe remediation actions.

Rules:
- Only propose actions from the allowed list in the runbook.
- Every action must have a rollback path.
- Cite specific evidence for each root cause.
- Return ONLY valid JSON, no markdown fences or extra text."""


def build_analysis_prompt(
    incident_id: str,
    namespace: str,
    workload: str,
    severity: str,
    raw_alert: str,
    evidence: dict[str, Any],
    runbook_title: str = "",
) -> str:
    """Build the user prompt for incident analysis."""
    evidence_text = _format_evidence(evidence)
    runbook_line = f"Runbook: {runbook_title}" if runbook_title else "Runbook: none"

    return f"""\
Analyze this incident and produce a remediation plan.

## Incident
- ID: {incident_id}
- Namespace: {namespace}
- Workload: {workload}
- Severity: {severity}
- Alert: {raw_alert}
- {runbook_line}

## Evidence
{evidence_text}

## Output Format
Return a JSON object with exactly this structure:
{{
    "summary": "plain language incident summary",
    "root_causes": [
        {{
            "cause": "string",
            "confidence": 0.0-1.0,
            "evidence": ["list of evidence that supports this"]
        }}
    ],
    "actions": [
        {{
            "name": "action_name e.g. rollout_restart, scale_replicas",
            "target": "target resource name",
            "parameters": {{}},
            "reason": "why this action helps"
        }}
    ]
}}"""


def _format_evidence(evidence: dict[str, Any]) -> str:
    """Format evidence dict into readable text."""
    parts: list[str] = []

    if evidence.get("pod_logs"):
        for pod, logs in evidence["pod_logs"].items():
            parts.append(f"Pod Logs ({pod}):\n{str(logs)[:500]}")

    if evidence.get("events"):
        for event in evidence["events"][:10]:
            reason = event.get("reason", "Unknown")
            message = event.get("message", "")
            parts.append(f"Event: {reason} — {message}")

    if evidence.get("deployment_status"):
        status = evidence["deployment_status"]
        parts.append(
            f"Deployment: desired={status.get('desired_replicas')}, "
            f"ready={status.get('ready_replicas')}, "
            f"available={status.get('available_replicas')}"
        )

    return "\n".join(parts) if parts else "No evidence collected."
