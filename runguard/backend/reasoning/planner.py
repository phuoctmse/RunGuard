"""LLM-based incident planner using Claude API."""

import json
from typing import Any

import anthropic

PLANNER_PROMPT = """\
You are an SRE incident analyst. Analyze the following incident \
and produce a remediation plan.

## Incident
- ID: {incident_id}
- Alert: {alert_summary}
- Runbook: {runbook_title}

## Evidence Collected
{evidence_text}

## Instructions
1. Summarize the incident in plain language.
2. Identify possible root causes with confidence scores (0.0-1.0).
3. Cite specific evidence that influenced each conclusion.
4. Propose remediation actions in priority order.
5. Each action must have: action name, target, priority, and reason.

## Output Format
Return a JSON object with exactly this structure:
{{
    "summary": "string - plain language incident summary",
    "root_causes": [
        {{
            "cause": "string",
            "confidence": 0.0-1.0,
            "evidence_refs": ["list of evidence that supports this"]
        }}
    ],
    "remediation_actions": [
        {{
            "action": "string - e.g. rollout_restart, scale_deployment",
            "target": "string - target resource name",
            "priority": 1,
            "reason": "string - why this action helps"
        }}
    ]
}}

Return ONLY the JSON object, no other text."""


class IncidentPlanner:
    """Generates remediation plans using Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    def _format_evidence(self, evidence: dict[str, Any]) -> str:
        """Format evidence dict into readable text for the prompt."""
        parts: list[str] = []
        if evidence.get("pod_logs"):
            for pod, logs in evidence["pod_logs"].items():
                parts.append(f"Pod Logs ({pod}):\n{logs[:500]}")
        if evidence.get("events"):
            for event in evidence["events"][:10]:
                reason = event.get("reason", "Unknown")
                message = event.get("message", "")
                parts.append(f"Event: {reason} - {message}")
        if evidence.get("deployment_status"):
            status = evidence["deployment_status"]
            desired = status.get("desired_replicas")
            ready = status.get("ready_replicas")
            available = status.get("available_replicas")
            parts.append(
                f"Deployment Status: desired={desired}, "
                f"ready={ready}, available={available}"
            )
        return "\n".join(parts) if parts else "No evidence collected"

    async def generate_plan(
        self,
        incident_id: str,
        alert_summary: str,
        evidence: dict[str, Any],
        runbook_title: str = "",
    ) -> dict[str, Any]:
        """Generate a remediation plan from evidence."""
        evidence_text = self._format_evidence(evidence)
        prompt = PLANNER_PROMPT.format(
            incident_id=incident_id,
            alert_summary=alert_summary,
            runbook_title=runbook_title,
            evidence_text=evidence_text,
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            content = text_blocks[0] if text_blocks else ""
            result: dict[str, Any] = json.loads(content)
            return result
        except Exception:
            return {
                "summary": "",
                "root_causes": [],
                "remediation_actions": [],
            }
