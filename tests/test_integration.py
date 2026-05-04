"""Integration test: runbook -> policy -> plan generation."""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from runguard.backend.compiler.parser import parse_runbook_markdown
from runguard.backend.compiler.extractor import extract_metadata
from runguard.backend.compiler.compiler import compile_runbook_to_policy
from runguard.backend.reasoning.planner import IncidentPlanner


SAMPLE_RUNBOOK = """# Pod CrashLoop Runbook

## Scope
- Namespaces: default, staging
- Workloads: web-app, api-server

## Allowed Tools
- rollout restart
- scale deployment

## Forbidden Tools
- delete deployment

## Severity
high

## Rollback Steps
1. kubectl rollout undo deployment/{name} -n {namespace}
"""


def test_runbook_to_policy_pipeline():
    """Full pipeline: markdown -> runbook -> policy."""
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    assert sections["title"] == "Pod CrashLoop Runbook"

    runbook = extract_metadata(sections, raw_markdown=SAMPLE_RUNBOOK)
    assert runbook.severity == "high"
    assert len(runbook.allowed_tools) == 2

    policy = compile_runbook_to_policy(runbook)
    assert policy.runbook_id == runbook.id
    assert len(policy.allowed_actions) == 2
    assert len(policy.forbidden_actions) == 1


@pytest.mark.asyncio
async def test_full_incident_flow():
    """Full flow: incident -> evidence -> plan via LLM."""
    # 1. Parse runbook
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    runbook = extract_metadata(sections, SAMPLE_RUNBOOK)
    policy = compile_runbook_to_policy(runbook)

    # 2. Mock evidence
    evidence = {
        "pod_logs": {"web-app-pod": "ERROR CrashLoopBackOff"},
        "events": [{"reason": "BackOff", "message": "container crash", "timestamp": "", "type": "Warning"}],
        "deployment_status": {"name": "web-app", "desired_replicas": 3, "ready_replicas": 0, "available_replicas": 0, "conditions": []},
    }

    # 3. Generate plan via LLM (mocked)
    planner = IncidentPlanner(api_key="test")
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "summary": "Pod crash loop due to container failure",
        "root_causes": [{"cause": "Application crash", "confidence": 0.9, "evidence_refs": ["pod logs"]}],
        "remediation_actions": [{"action": "rollout_restart", "target": "web-app", "priority": 1, "reason": "Restart crashed pod"}],
    }))]

    with patch.object(planner.client.messages, "create", new_callable=AsyncMock, return_value=mock_response):
        plan = await planner.generate_plan(
            incident_id="inc-001",
            alert_summary="Pod CrashLoopBackOff",
            evidence=evidence,
            runbook_title=runbook.title,
        )

    assert plan["summary"] != ""
    assert len(plan["root_causes"]) == 1
    assert policy.allowed_actions[0].name == "rollout_restart"
