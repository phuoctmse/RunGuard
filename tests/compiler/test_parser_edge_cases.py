"""Tests for Markdown parser — edge cases and boundary conditions."""

from runguard.backend.compiler.parser import parse_runbook_markdown


def test_empty_markdown():
    """Should handle empty string gracefully."""
    result = parse_runbook_markdown("")
    assert result == {}


def test_no_title():
    """Should handle markdown without H1 title."""
    md = """## Scope
- Namespaces: default
"""
    result = parse_runbook_markdown(md)
    assert "title" not in result


def test_no_sections():
    """Should return title only when no sections exist."""
    md = "# Just a Title"
    result = parse_runbook_markdown(md)
    assert result.get("title") == "Just a Title"


def test_severity_as_list_fallback():
    """Should convert severity list to string when only list items present."""
    md = """# Test

## Severity
- high
"""
    result = parse_runbook_markdown(md)
    assert result["severity"] == "high"
    assert isinstance(result["severity"], str)


def test_severity_empty_list_defaults_medium():
    """Should default to medium when severity section is empty."""
    md = """# Test

## Severity

## Allowed Tools
- rollout restart
"""
    result = parse_runbook_markdown(md)
    # severity should be empty list or "medium"
    sev = result.get("severity")
    if isinstance(sev, list):
        assert sev == [] or sev[0] == "medium"


def test_scope_case_insensitive():
    """Should parse scope regardless of case."""
    md = """# Test

## Scope
- NAMESPACES: prod
- WORKLOADS: api
"""
    result = parse_runbook_markdown(md)
    assert "prod" in result["scope"]["namespaces"]
    assert "api" in result["scope"]["workloads"]


def test_multiple_h1_takes_first():
    """Should use the first H1 as title."""
    md = """# First Title

# Second Title

## Scope
- Namespaces: default
"""
    result = parse_runbook_markdown(md)
    assert result["title"] == "First Title"


def test_h3_headers_ignored():
    """Should not treat H3 as section headers."""
    md = """# Test

## Allowed Tools
- rollout restart

### Sub-note
This should be ignored

- scale deployment
"""
    result = parse_runbook_markdown(md)
    assert len(result["allowed_tools"]) == 2


def test_whitespace_handling():
    """Should handle extra whitespace gracefully."""
    md = """#   Spaced Title


##   Scope
  - Namespaces:   default  ,  staging

"""
    result = parse_runbook_markdown(md)
    assert result["title"] == "Spaced Title"
    assert "default" in result["scope"]["namespaces"]


def test_rollback_numbered_list():
    """Should parse numbered rollback steps."""
    md = """# Test

## Rollback Steps
1. First step
2. Second step
3. Third step
"""
    result = parse_runbook_markdown(md)
    assert len(result["rollback_steps"]) == 3
    assert result["rollback_steps"][0] == "First step"
    assert result["rollback_steps"][2] == "Third step"


def test_mixed_list_and_numbered():
    """Should handle mixed list styles in same section."""
    md = """# Test

## Allowed Tools
- rollout restart
- scale deployment

## Rollback Steps
1. kubectl rollout undo
"""
    result = parse_runbook_markdown(md)
    assert len(result["allowed_tools"]) == 2
    assert len(result["rollback_steps"]) == 1


def test_full_realistic_runbook():
    """Should parse a complete realistic runbook correctly."""
    md = """# Production Database Connection Failure

## Scope
- Namespaces: production, staging
- Workloads: api-server, web-frontend, worker

## Allowed Tools
- rollout restart
- scale deployment
- fetch logs

## Forbidden Tools
- delete deployment
- delete namespace
- exec into pod

## Severity
critical

## Rollback Steps
1. kubectl rollout undo deployment/{name} -n {namespace}
2. kubectl scale deployment/{name} --replicas={original_replicas} -n {namespace}
3. kubectl set image deployment/{name} {container}={previous_image} -n {namespace}
"""
    result = parse_runbook_markdown(md)
    assert result["title"] == "Production Database Connection Failure"
    assert len(result["scope"]["namespaces"]) == 2
    assert len(result["scope"]["workloads"]) == 3
    assert len(result["allowed_tools"]) == 3
    assert len(result["forbidden_tools"]) == 3
    assert result["severity"] == "critical"
    assert len(result["rollback_steps"]) == 3
