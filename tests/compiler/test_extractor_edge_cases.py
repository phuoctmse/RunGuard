"""Tests for runbook metadata extractor — edge cases."""

from runguard.backend.compiler.extractor import extract_metadata


def test_extract_with_empty_sections():
    """Should handle empty sections dict."""
    result = extract_metadata({}, raw_markdown="# empty")
    assert result.title == "Untitled Runbook"
    assert result.scope == {}
    assert result.allowed_tools == []
    assert result.forbidden_tools == []
    assert result.severity == "medium"
    assert result.rollback_steps == []


def test_extract_scope_as_list_fallback():
    """Should fallback to empty scope when scope is a list (not dict)."""
    sections = {
        "title": "Test",
        "scope": ["invalid", "format"],
    }
    result = extract_metadata(sections, raw_markdown="# test")
    assert result.scope == {"namespaces": [], "workloads": []}


def test_extract_preserves_raw_markdown():
    """Should store raw markdown in the runbook."""
    md = "# Test Runbook\n\nSome content"
    result = extract_metadata({"title": "Test"}, raw_markdown=md)
    assert result.raw_markdown == md


def test_extract_generates_unique_ids():
    """Should generate unique IDs for each runbook."""
    sections = {"title": "Test"}
    ids = set()
    for _ in range(100):
        r = extract_metadata(sections)
        ids.add(r.id)
    assert len(ids) == 100


def test_extract_id_format():
    """Should generate IDs with rb- prefix."""
    result = extract_metadata({"title": "Test"})
    assert result.id.startswith("rb-")
    assert len(result.id) == 11  # rb- + 8 hex chars


def test_extract_partial_sections():
    """Should handle sections dict with only some keys."""
    sections = {
        "title": "Partial",
        "allowed_tools": ["rollout restart"],
    }
    result = extract_metadata(sections)
    assert result.title == "Partial"
    assert result.allowed_tools == ["rollout restart"]
    assert result.forbidden_tools == []
    assert result.severity == "medium"
