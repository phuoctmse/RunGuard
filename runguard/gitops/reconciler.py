"""GitOps reconciler — manifest patches and git commits for K8s remediation."""

import json
import subprocess
from pathlib import Path
from typing import Any

from runguard.backend.audit.store import AuditStore
from runguard.backend.models.audit import AuditRecord
from runguard.gitops.models import (
    GitOpsCommit,
    ManifestPatch,
    ReconciliationResult,
    ReconciliationStatus,
)


class GitOpsReconciler:
    """Generates manifest patches and git commits for GitOps-based remediation.

    When GitOps mode is enabled, remediation changes go through git
    instead of direct K8s API calls.
    """

    def __init__(
        self,
        repo_path: str,
        audit_store: AuditStore | None = None,
        branch: str = "main",
    ) -> None:
        self.repo_path = Path(repo_path)
        self.audit_store = audit_store
        self.branch = branch

    def generate_manifest_patch(
        self,
        resource_kind: str,
        resource_name: str,
        namespace: str,
        changes: dict[str, Any],
        description: str = "",
    ) -> ManifestPatch:
        """Generate a manifest patch for a K8s resource.

        Args:
            resource_kind: Kind of resource (Deployment, Service, etc.)
            resource_name: Name of the resource
            namespace: Kubernetes namespace
            changes: Dict of field paths to new values
            description: Human-readable description of the change

        Returns:
            ManifestPatch with the generated patch content
        """
        patch_content = json.dumps({"spec": changes}, indent=2, default=str)
        return ManifestPatch(
            resource_kind=resource_kind,
            resource_name=resource_name,
            namespace=namespace,
            patch_type="strategic-merge",
            patch_content=patch_content,
            description=description or f"Patch {resource_kind}/{resource_name}",
        )

    def generate_replica_patch(
        self, deployment_name: str, namespace: str, replicas: int
    ) -> ManifestPatch:
        """Generate a patch to scale a deployment."""
        return self.generate_manifest_patch(
            resource_kind="Deployment",
            resource_name=deployment_name,
            namespace=namespace,
            changes={"replicas": replicas},
            description=f"Scale {deployment_name} to {replicas} replicas",
        )

    def generate_image_patch(
        self, deployment_name: str, namespace: str, container_name: str, image: str
    ) -> ManifestPatch:
        """Generate a patch to update a container image."""
        return ManifestPatch(
            resource_kind="Deployment",
            resource_name=deployment_name,
            namespace=namespace,
            patch_type="strategic-merge",
            patch_content=json.dumps(
                {
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": [{"name": container_name, "image": image}]
                            }
                        }
                    }
                },
                indent=2,
            ),
            description=f"Update {container_name} image to {image}",
        )

    def create_remediation_commit(
        self, incident_id: str, patches: list[ManifestPatch]
    ) -> GitOpsCommit:
        """Create a git commit with manifest patches.

        Writes patched manifests to the repo and commits them.

        Args:
            incident_id: The incident this commit addresses
            patches: List of manifest patches to apply

        Returns:
            GitOpsCommit with the commit hash and metadata

        Raises:
            RuntimeError: If git operations fail
        """
        commit_message = (
            f"runguard(remediation): {incident_id} - {len(patches)} patch(es)"
        )

        # Write patches to manifest directory
        manifests_dir = self.repo_path / "manifests" / incident_id
        manifests_dir.mkdir(parents=True, exist_ok=True)

        for i, patch in enumerate(patches):
            fname = f"{patch.resource_kind.lower()}_{patch.resource_name}_{i}.json"
            patch_file = manifests_dir / fname
            patch_file.write_text(patch.patch_content, encoding="utf-8")

        # Git add and commit
        try:
            self._git_add(str(manifests_dir))
            self._git_commit(commit_message)
            commit_hash = self._get_head_hash()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Git operation failed: {e}") from e

        commit = GitOpsCommit(
            commit_hash=commit_hash,
            branch=self.branch,
            message=commit_message,
            manifests=patches,
        )

        # Record in audit store
        if self.audit_store:
            record = AuditRecord(
                id=f"gitops-{commit_hash[:8]}",
                incident_id=incident_id,
                event_type="gitops_commit",
                details={
                    "commit_hash": commit_hash,
                    "branch": self.branch,
                    "patch_count": len(patches),
                    "manifests": [
                        {
                            "kind": p.resource_kind,
                            "name": p.resource_name,
                            "namespace": p.namespace,
                        }
                        for p in patches
                    ],
                },
            )
            self.audit_store.write(record)

        return commit

    def check_reconciliation_status(
        self, commit_hash: str, reconciler: str = "flux"
    ) -> ReconciliationResult:
        """Check if a GitOps commit has been reconciled.

        This checks the cluster for reconciliation status from
        Flux or ArgoCD.

        Args:
            commit_hash: The git commit hash to check
            reconciler: The GitOps reconciler type ("flux" or "argocd")

        Returns:
            ReconciliationResult with the current status
        """
        # In a real implementation, this would query Flux/ArgoCD CRDs
        # For MVP, we check if the commit exists in the repo
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-1", commit_hash],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0:
                return ReconciliationResult(
                    commit_hash=commit_hash,
                    status=ReconciliationStatus.PENDING,
                    reconciler=reconciler,
                    message="Commit exists, awaiting reconciliation",
                )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return ReconciliationResult(
            commit_hash=commit_hash,
            status=ReconciliationStatus.FAILED,
            reconciler=reconciler,
            message="Commit not found in repository",
        )

    def _git_add(self, path: str) -> None:
        """Stage files for commit."""
        try:
            subprocess.run(
                ["git", "add", path],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"git add failed: {e.stderr}") from e

    def _git_commit(self, message: str) -> None:
        """Create a git commit."""
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"git commit failed: {e.stderr}") from e

    def _get_head_hash(self) -> str:
        """Get the HEAD commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"git rev-parse failed: {e.stderr}") from e
