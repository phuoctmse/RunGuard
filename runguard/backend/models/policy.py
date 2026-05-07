"""Policy data model."""

from pydantic import BaseModel


class PolicyScope(BaseModel):
    """Scope constraints for a policy."""

    namespaces: list[str] = []
    workloads: list[str] = []


class AllowedAction(BaseModel):
    """An action permitted by the policy."""

    name: str
    blast_radius: str = "low"  # low, medium, high
    requires_approval: bool = False
    rollback_path: list[str] = []


class ForbiddenAction(BaseModel):
    """An action forbidden by the policy."""

    name: str
    reason: str = ""


class Policy(BaseModel):
    """Machine-enforceable policy generated from a Runbook."""

    id: str
    runbook_id: str
    scope: PolicyScope = PolicyScope()
    allowed_actions: list[AllowedAction] = []
    forbidden_actions: list[ForbiddenAction] = []
    severity: str = "medium"
    max_blast_radius_threshold: float = 0.3
