"""Compile a Runbook into a machine-enforceable Policy."""

import uuid

from runguard.backend.models.policy import AllowedAction, ForbiddenAction, Policy
from runguard.backend.models.runbook import Runbook

# Map tool names to action identifiers
TOOL_TO_ACTION = {
    "rollout restart": "rollout_restart",
    "scale deployment": "scale_deployment",
    "fetch logs": "fetch_logs",
    "run job": "run_job",
    "trigger ssm": "trigger_ssm",
}

# Blast radius defaults per action type
BLAST_RADIUS = {
    "rollout_restart": "low",
    "scale_deployment": "medium",
    "fetch_logs": "none",
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

    return Policy(
        id=policy_id,
        runbook_id=runbook.id,
        allowed_actions=allowed_actions,
        forbidden_actions=forbidden_actions,
        max_blast_radius_threshold=0.3,
    )
