"""Policy data model."""

from pydantic import BaseModel


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
    allowed_actions: list[AllowedAction] = []
    forbidden_actions: list[ForbiddenAction] = []
    max_blast_radius_threshold: float = 0.3
