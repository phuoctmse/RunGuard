"""Tests for policy validation engine."""

import pytest

from runguard.backend.models.policy import AllowedAction, ForbiddenAction, Policy
from runguard.backend.policy.engine import PolicyEngine


@pytest.fixture
def policy_engine():
    return PolicyEngine()


@pytest.fixture
def sample_policy():
    return Policy(
        id="pol-001",
        runbook_id="rb-001",
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


def test_validate_scope_violation(policy_engine):
    policy = Policy(
        id="pol-002",
        runbook_id="rb-002",
        allowed_actions=[
            AllowedAction(
                name="rollout_restart", blast_radius="low", requires_approval=False
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


def test_validate_plan(policy_engine, sample_policy):
    actions = ["rollout_restart", "scale_deployment", "delete_deployment"]
    results = policy_engine.validate_plan(
        actions, sample_policy, namespace="default", environment="dev"
    )
    assert len(results) == 3
    assert results[0]["status"] == "approved"
    assert results[1]["status"] == "requires_approval"
    assert results[2]["status"] == "blocked"
