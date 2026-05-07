"""Tests for Runbook -> Policy compiler — edge cases."""

from runguard.backend.compiler.compiler import compile_runbook_to_policy, TOOL_TO_ACTION, BLAST_RADIUS
from runguard.backend.models.runbook import Runbook


def test_compile_empty_allowed_tools():
    """Should produce policy with no allowed actions."""
    runbook = Runbook(
        id="rb-empty",
        title="Empty",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=[],
        forbidden_tools=["delete deployment"],
        severity="low",
        rollback_steps=["undo"],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.allowed_actions == []
    assert len(policy.forbidden_actions) == 1


def test_compile_unknown_tool():
    """Should handle unknown tool names gracefully."""
    runbook = Runbook(
        id="rb-unknown",
        title="Unknown Tool",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["custom action"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=["undo"],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.allowed_actions[0].name == "custom_action"


def test_compile_fetch_logs_no_approval():
    """fetch_logs should not require approval (blast_radius=none)."""
    runbook = Runbook(
        id="rb-logs",
        title="Logs Only",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["fetch logs"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=["undo"],
    )
    policy = compile_runbook_to_policy(runbook)
    action = policy.allowed_actions[0]
    assert action.name == "fetch_logs"
    assert action.blast_radius == "none"
    assert action.requires_approval is False


def test_compile_all_tools():
    """Should handle all known tools correctly."""
    runbook = Runbook(
        id="rb-all",
        title="All Tools",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["rollout restart", "scale deployment", "fetch logs", "run job", "trigger ssm"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=["undo"],
    )
    policy = compile_runbook_to_policy(runbook)
    names = [a.name for a in policy.allowed_actions]
    assert "rollout_restart" in names
    assert "scale_deployment" in names
    assert "fetch_logs" in names
    assert "run_job" in names
    assert "trigger_ssm" in names


def test_compile_policy_id_format():
    """Should generate policy ID with pol- prefix."""
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["fetch logs"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=["undo"],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.id.startswith("pol-")
    assert len(policy.id) == 12  # pol- + 8 hex chars


def test_compile_preserves_runbook_id():
    """Should reference the original runbook ID."""
    runbook = Runbook(
        id="rb-custom-123",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["fetch logs"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=["undo"],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.runbook_id == "rb-custom-123"


def test_compile_max_blast_radius_threshold():
    """Should set max_blast_radius_threshold to 0.3."""
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=[],
        forbidden_tools=[],
        severity="low",
        rollback_steps=[],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.max_blast_radius_threshold == 0.3


def test_compile_forbidden_preserves_reason():
    """Forbidden actions should have reason='forbidden by runbook'."""
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=[],
        forbidden_tools=["delete pod"],
        severity="low",
        rollback_steps=[],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.forbidden_actions[0].reason == "forbidden by runbook"


def test_compile_with_rollback_assigns_rollback_path():
    """Allowed actions should include rollback_path when runbook has rollback steps."""
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["fetch logs"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=["kubectl rollout undo deployment/{name}"],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.allowed_actions[0].rollback_path == ["kubectl rollout undo deployment/{name}"]


def test_compile_without_rollback_empty_path():
    """Allowed actions should have empty rollback_path when no rollback steps."""
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["fetch logs"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=[],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.allowed_actions[0].rollback_path == []


def test_tool_to_action_mapping_completeness():
    """TOOL_TO_ACTION should map all standard tools (both formats)."""
    expected_tools = {
        # Spec format (underscore)
        "rollout_restart",
        "scale_replicas",
        "update_image",
        "delete_pod",
        "fetch_logs",
        "patch_config",
        # Legacy format (space-separated)
        "rollout restart",
        "scale deployment",
        "scale replicas",
        "update image",
        "delete pod",
        "fetch logs",
        "patch config",
        "run job",
        "trigger ssm",
    }
    assert set(TOOL_TO_ACTION.keys()) == expected_tools


def test_blast_radius_mapping_completeness():
    """BLAST_RADIUS should cover all mapped actions."""
    for action_name in TOOL_TO_ACTION.values():
        assert action_name in BLAST_RADIUS, f"Missing blast radius for {action_name}"
