"""Compile a Runbook into a machine-enforceable Policy."""

import uuid

from runguard.backend.models.policy import (
    AllowedAction,
    ForbiddenAction,
    Policy,
    PolicyScope,
)
from runguard.backend.models.runbook import Runbook

# Map tool names to action identifiers
# Accepts both space-separated (legacy) and underscore (spec) formats
TOOL_TO_ACTION = {
    # Spec format (underscore)
    "rollout_restart": "rollout_restart",
    "scale_replicas": "scale_replicas",
    "update_image": "update_image",
    "delete_pod": "delete_pod",
    "fetch_logs": "fetch_logs",
    "patch_config": "patch_config",
    # Legacy format (space-separated) — backward compatibility
    "rollout restart": "rollout_restart",
    "scale deployment": "scale_deployment",
    "scale replicas": "scale_replicas",
    "update image": "update_image",
    "delete pod": "delete_pod",
    "fetch logs": "fetch_logs",
    "patch config": "patch_config",
    "run job": "run_job",
    "trigger ssm": "trigger_ssm",
}

# Blast radius defaults per action type
BLAST_RADIUS = {
    "rollout_restart": "low",
    "scale_deployment": "medium",
    "scale_replicas": "medium",
    "update_image": "medium",
    "delete_pod": "high",
    "fetch_logs": "none",
    "patch_config": "medium",
    "run_job": "medium",
    "trigger_ssm": "medium",
}


def compile_runbook_to_policy(runbook: Runbook) -> Policy:
    """Convert a Runbook into a Policy with action classifications."""
    policy_id = f"pol-{uuid.uuid4().hex[:8]}"

    allowed_actions = []
    has_rollback = len(runbook.rollback_steps) > 0

    for tool in runbook.allowed_tools:
        action_name = TOOL_TO_ACTION.get(tool, tool.replace(" ", "_"))
        blast_radius = BLAST_RADIUS.get(action_name, "medium")

        # Actions without rollback path require approval
        requires_approval = not has_rollback or blast_radius in ("medium", "high")

        allowed_actions.append(
            AllowedAction(
                name=action_name,
                blast_radius=blast_radius,
                requires_approval=requires_approval,
                rollback_path=runbook.rollback_steps if has_rollback else [],
            )
        )

    forbidden_actions = [
        ForbiddenAction(
            name=tool.replace(" ", "_"),
            reason="forbidden by runbook",
        )
        for tool in runbook.forbidden_tools
    ]

    scope = PolicyScope(
        namespaces=runbook.scope.get("namespaces", []),
        workloads=runbook.scope.get("workloads", []),
    )

    return Policy(
        id=policy_id,
        runbook_id=runbook.id,
        scope=scope,
        allowed_actions=allowed_actions,
        forbidden_actions=forbidden_actions,
        severity=runbook.severity,
        max_blast_radius_threshold=0.3,
    )
