"""Tests for policy validation engine."""

import pytest

from runguard.backend.models.policy import (
    AllowedAction,
    ForbiddenAction,
    Policy,
    PolicyScope,
)
from runguard.backend.policy.engine import MAX_AUTO_APPROVED_PER_INCIDENT, PolicyEngine


@pytest.fixture
def policy_engine():
    return PolicyEngine()


@pytest.fixture
def sample_policy():
    return Policy(
        id="pol-001",
        runbook_id="rb-001",
        scope=PolicyScope(namespaces=["default", "staging"]),
        allowed_actions=[
            AllowedAction(
                name="rollout_restart",
                blast_radius="low",
                requires_approval=False,
                rollback_path=["undo"],
            ),
            AllowedAction(
                name="scale_deployment",
                blast_radius="medium",
                requires_approval=True,
                rollback_path=["scale back"],
            ),
        ],
        forbidden_actions=[
            ForbiddenAction(name="delete_deployment", reason="forbidden")
        ],
        severity="high",
        max_blast_radius_threshold=0.3,
    )


def test_validate_approved_action(policy_engine, sample_policy):
    result = policy_engine.validate_action(
        "rollout_restart", sample_policy, namespace="default", environment="dev"
    )
    assert result["status"] == "approved"


def test_validate_requires_approval(policy_engine, sample_policy):
    result = policy_engine.validate_action(
        "scale_deployment", sample_policy, namespace="default", environment="dev"
    )
    assert result["status"] == "requires_approval"


def test_validate_forbidden_action(policy_engine, sample_policy):
    result = policy_engine.validate_action(
        "delete_deployment", sample_policy, namespace="default", environment="dev"
    )
    assert result["status"] == "blocked"
    assert "forbidden" in result["reason"].lower()


def test_validate_unknown_action(policy_engine, sample_policy):
    result = policy_engine.validate_action(
        "unknown_action", sample_policy, namespace="default", environment="dev"
    )
    assert result["status"] == "blocked"


def test_validate_production_requires_approval(policy_engine, sample_policy):
    result = policy_engine.validate_action(
        "rollout_restart",
        sample_policy,
        namespace="default",
        environment="production",
    )
    assert result["status"] == "requires_approval"


def test_validate_scope_violation_from_policy_scope(policy_engine, sample_policy):
    """Namespace outside policy scope should be blocked."""
    result = policy_engine.validate_action(
        "rollout_restart",
        sample_policy,
        namespace="kube-system",
        environment="dev",
    )
    assert result["status"] == "blocked"
    assert "scope" in result["reason"].lower()


def test_validate_scope_violation_from_allowed_namespaces(policy_engine):
    """Explicit allowed_namespaces override policy scope."""
    policy = Policy(
        id="pol-002",
        runbook_id="rb-002",
        allowed_actions=[
            AllowedAction(
                name="rollout_restart", blast_radius="low", rollback_path=["undo"]
            )
        ],
        forbidden_actions=[],
    )
    result = policy_engine.validate_action(
        "rollout_restart",
        policy,
        namespace="kube-system",
        environment="dev",
        allowed_namespaces=["default", "staging"],
    )
    assert result["status"] == "blocked"
    assert "scope" in result["reason"].lower()


def test_validate_no_rollback_requires_approval(policy_engine):
    """Action without rollback path should require approval."""
    policy = Policy(
        id="pol-003",
        runbook_id="rb-003",
        allowed_actions=[
            AllowedAction(
                name="rollout_restart", blast_radius="low", rollback_path=[]
            )
        ],
        forbidden_actions=[],
    )
    result = policy_engine.validate_action(
        "rollout_restart", policy, namespace="default", environment="dev"
    )
    assert result["status"] == "requires_approval"
    assert "rollback" in result["reason"].lower()


def test_validate_auto_approve_limit(policy_engine, sample_policy):
    """Should require approval when auto-approve limit is reached."""
    result = policy_engine.validate_action(
        "rollout_restart",
        sample_policy,
        namespace="default",
        environment="dev",
        auto_approved_count=MAX_AUTO_APPROVED_PER_INCIDENT,
    )
    assert result["status"] == "requires_approval"
    assert "limit" in result["reason"].lower()


def test_validate_auto_approve_under_limit(policy_engine, sample_policy):
    """Should approve when under auto-approve limit."""
    result = policy_engine.validate_action(
        "rollout_restart",
        sample_policy,
        namespace="default",
        environment="dev",
        auto_approved_count=MAX_AUTO_APPROVED_PER_INCIDENT - 1,
    )
    assert result["status"] == "approved"


def test_validate_plan(policy_engine, sample_policy):
    actions = ["rollout_restart", "scale_deployment", "delete_deployment"]
    results = policy_engine.validate_plan(
        actions, sample_policy, namespace="default", environment="dev"
    )
    assert len(results) == 3
    assert results[0]["status"] == "approved"
    assert results[1]["status"] == "requires_approval"
    assert results[2]["status"] == "blocked"


def test_validate_plan_tracks_auto_approved_count(policy_engine, sample_policy):
    """Plan validation should increment auto-approved count across actions."""
    # Use many low-risk actions to test counter
    policy = Policy(
        id="pol-multi",
        runbook_id="rb-multi",
        allowed_actions=[
            AllowedAction(
                name=f"action_{i}",
                blast_radius="low",
                rollback_path=["undo"],
            )
            for i in range(10)
        ],
        forbidden_actions=[],
    )
    actions = [f"action_{i}" for i in range(10)]
    results = policy_engine.validate_plan(
        actions, policy, namespace="default", environment="dev"
    )
    # First 5 should be approved, rest should require_approval
    for i in range(MAX_AUTO_APPROVED_PER_INCIDENT):
        assert results[i]["status"] == "approved", f"action_{i} should be approved"
    for i in range(MAX_AUTO_APPROVED_PER_INCIDENT, 10):
        assert results[i]["status"] == "requires_approval", (
            f"action_{i} should require approval"
        )
