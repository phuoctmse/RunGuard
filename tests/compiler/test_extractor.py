"""Tests for runbook metadata extractor."""

from runguard.backend.compiler.extractor import extract_metadata


SECTIONS = {
    "title": "Pod CrashLoop Runbook",
    "scope": {"namespaces": ["default"], "workloads": ["web-app"]},
    "allowed_tools": ["rollout restart", "scale deployment"],
    "forbidden_tools": ["delete deployment"],
    "severity": "high",
    "rollback_steps": [
        "kubectl rollout undo deployment/{name} -n {namespace}",
    ],
}


def test_extract_metadata_produces_runbook():
    metadata = extract_metadata(SECTIONS, raw_markdown="# test")
    assert metadata.id is not None
    assert metadata.title == "Pod CrashLoop Runbook"
    assert metadata.severity == "high"


def test_extract_metadata_generates_id():
    m1 = extract_metadata(SECTIONS, raw_markdown="# test")
    m2 = extract_metadata(SECTIONS, raw_markdown="# test")
    assert m1.id != m2.id


def test_extract_metadata_scope():
    metadata = extract_metadata(SECTIONS, raw_markdown="# test")
    assert "default" in metadata.scope["namespaces"]
    assert "web-app" in metadata.scope["workloads"]
