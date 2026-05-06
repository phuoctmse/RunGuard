"""Pydantic models for GitOps operations."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReconciliationStatus(StrEnum):
    """Status of a GitOps reconciliation attempt."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class ManifestPatch(BaseModel):
    """A proposed change to a Kubernetes manifest."""

    resource_kind: str
    resource_name: str
    namespace: str
    patch_type: str  # strategic-merge, json, merge
    patch_content: str
    description: str = ""


class GitOpsCommit(BaseModel):
    """Record of a Git commit for GitOps remediation."""

    commit_hash: str
    branch: str
    message: str
    manifests: list[ManifestPatch] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReconciliationResult(BaseModel):
    """Result of checking reconciliation status."""

    commit_hash: str
    status: ReconciliationStatus
    reconciler: str  # flux, argocd
    message: str = ""
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
