"""Tests for Runbook -> Policy compiler."""

from runguard.backend.compiler.compiler import compile_runbook_to_policy
from runguard.backend.models.runbook import Runbook


def test_compile_produces_policy():
    runbook = Runbook(
        id="rb-test",
        title="Test Runbook",
        scope={"namespaces": ["default"], "workloads": ["web-app"]},
        allowed_tools=["rollout restart", "scale deployment"],
        forbidden_tools=["delete deployment"],
        severity="high",
        rollback_steps=["kubectl rollout undo deployment/{name} -n {namespace}"],
    )
    policy = compile_runbook_to_policy(runbook)
    assert policy.runbook_id == "rb-test"
    assert len(policy.allowed_actions) == 2
    assert len(policy.forbidden_actions) == 1


def test_compile_maps_tool_to_action():
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["rollout restart"],
        forbidden_tools=[],
        severity="low",
        rollback_steps=["kubectl rollout undo deployment/{name}"],
    )
    policy = compile_runbook_to_policy(runbook)
    action_names = [a.name for a in policy.allowed_actions]
    assert "rollout_restart" in action_names


def test_compile_no_rollback_marks_approval_required():
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=["scale deployment"],
        forbidden_tools=[],
        severity="medium",
        rollback_steps=[],
    )
    policy = compile_runbook_to_policy(runbook)
    scale_action = [a for a in policy.allowed_actions if a.name == "scale_deployment"][0]
    assert scale_action.requires_approval is True


def test_compile_forbidden_actions():
    runbook = Runbook(
        id="rb-test",
        title="Test",
        scope={"namespaces": ["default"], "workloads": ["*"]},
        allowed_tools=[],
        forbidden_tools=["delete deployment", "delete namespace"],
        severity="high",
        rollback_steps=[],
    )
    policy = compile_runbook_to_policy(runbook)
    assert len(policy.forbidden_actions) == 2
    forbidden_names = [f.name for f in policy.forbidden_actions]
    assert "delete_deployment" in forbidden_names
