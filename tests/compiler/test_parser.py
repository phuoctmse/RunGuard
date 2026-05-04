"""Tests for Markdown runbook parser."""

from runguard.backend.compiler.parser import parse_runbook_markdown


SAMPLE_RUNBOOK = """# Pod CrashLoop Runbook

## Scope
- Namespaces: default, staging
- Workloads: web-app, api-server

## Allowed Tools
- rollout restart
- scale deployment
- fetch logs

## Forbidden Tools
- delete deployment
- delete namespace

## Severity
high

## Rollback Steps
1. kubectl rollout undo deployment/{name} -n {namespace}
2. kubectl scale deployment/{name} --replicas={original_replicas} -n {namespace}
"""


def test_parse_sections():
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    assert "scope" in sections
    assert "allowed_tools" in sections
    assert "forbidden_tools" in sections
    assert "severity" in sections
    assert "rollback_steps" in sections


def test_parse_scope():
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    assert "default" in sections["scope"]["namespaces"]
    assert "staging" in sections["scope"]["namespaces"]
    assert "web-app" in sections["scope"]["workloads"]


def test_parse_allowed_tools():
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    assert "rollout restart" in sections["allowed_tools"]
    assert len(sections["allowed_tools"]) == 3


def test_parse_forbidden_tools():
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    assert "delete deployment" in sections["forbidden_tools"]
    assert len(sections["forbidden_tools"]) == 2


def test_parse_severity():
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    assert sections["severity"] == "high"


def test_parse_rollback_steps():
    sections = parse_runbook_markdown(SAMPLE_RUNBOOK)
    assert len(sections["rollback_steps"]) == 2
    assert "rollout undo" in sections["rollback_steps"][0]


def test_missing_rollback_raises_error():
    bad_runbook = """# Bad Runbook

## Scope
- Namespaces: default

## Severity
low
"""
    sections = parse_runbook_markdown(bad_runbook)
    assert sections.get("rollback_steps") is None or len(sections.get("rollback_steps", [])) == 0
