"""Tests for GitOps reconciler."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runguard.backend.audit.store import AuditStore
from runguard.gitops.models import ReconciliationStatus
from runguard.gitops.reconciler import GitOpsReconciler


@pytest.fixture
def audit_store(tmp_path):
    return AuditStore(store_path=str(tmp_path / "audit"))


@pytest.fixture
def reconciler(tmp_path, audit_store):
    repo = tmp_path / "repo"
    repo.mkdir()
    return GitOpsReconciler(repo_path=str(repo), audit_store=audit_store)


def test_generate_manifest_patch(reconciler):
    patch = reconciler.generate_manifest_patch(
        resource_kind="Deployment",
        resource_name="my-app",
        namespace="default",
        changes={"replicas": 3},
        description="Scale to 3",
    )
    assert patch.resource_kind == "Deployment"
    assert patch.resource_name == "my-app"
    assert patch.namespace == "default"
    assert patch.patch_type == "strategic-merge"
    parsed = json.loads(patch.patch_content)
    assert parsed["spec"]["replicas"] == 3


def test_generate_replica_patch(reconciler):
    patch = reconciler.generate_replica_patch("my-app", "default", 5)
    assert patch.resource_kind == "Deployment"
    assert patch.resource_name == "my-app"
    parsed = json.loads(patch.patch_content)
    assert parsed["spec"]["replicas"] == 5
    assert "5 replicas" in patch.description


def test_generate_image_patch(reconciler):
    patch = reconciler.generate_image_patch(
        "my-app", "default", "web", "nginx:1.25"
    )
    assert patch.resource_kind == "Deployment"
    parsed = json.loads(patch.patch_content)
    containers = parsed["spec"]["template"]["spec"]["containers"]
    assert containers[0]["name"] == "web"
    assert containers[0]["image"] == "nginx:1.25"


@patch.object(GitOpsReconciler, "_git_add")
@patch.object(GitOpsReconciler, "_git_commit")
@patch.object(GitOpsReconciler, "_get_head_hash", return_value="abc123def456abc123def456abc123def456abc1")
def test_create_remediation_commit(mock_hash, mock_commit, mock_add, reconciler):
    patches = [
        reconciler.generate_replica_patch("my-app", "default", 3),
    ]
    commit = reconciler.create_remediation_commit("inc-001", patches)
    assert commit.commit_hash == "abc123def456abc123def456abc123def456abc1"
    assert commit.branch == "main"
    assert "inc-001" in commit.message
    assert len(commit.manifests) == 1
    mock_add.assert_called_once()
    mock_commit.assert_called_once()


@patch.object(GitOpsReconciler, "_git_add")
@patch.object(GitOpsReconciler, "_git_commit")
@patch.object(GitOpsReconciler, "_get_head_hash", return_value="abc123def456abc123def456abc123def456abc1")
def test_create_commit_writes_manifests(mock_hash, mock_commit, mock_add, reconciler, tmp_path):
    patches = [
        reconciler.generate_replica_patch("my-app", "default", 3),
    ]
    reconciler.create_remediation_commit("inc-002", patches)
    manifest_dir = Path(reconciler.repo_path) / "manifests" / "inc-002"
    assert manifest_dir.exists()
    files = list(manifest_dir.iterdir())
    assert len(files) == 1
    content = json.loads(files[0].read_text(encoding="utf-8"))
    assert content["spec"]["replicas"] == 3


@patch.object(GitOpsReconciler, "_git_add")
@patch.object(GitOpsReconciler, "_git_commit")
@patch.object(GitOpsReconciler, "_get_head_hash", return_value="abc123def456abc123def456abc123def456abc1")
def test_create_commit_records_in_audit(mock_hash, mock_commit, mock_add, reconciler, audit_store):
    patches = [
        reconciler.generate_replica_patch("my-app", "default", 3),
    ]
    reconciler.create_remediation_commit("inc-003", patches)
    records = audit_store.read("inc-003")
    assert len(records) == 1
    assert records[0].event_type == "gitops_commit"
    assert records[0].details["patch_count"] == 1


@patch("subprocess.run")
def test_check_reconciliation_status_found(mock_run, reconciler):
    mock_run.return_value = MagicMock(returncode=0)
    result = reconciler.check_reconciliation_status("abc123def456abc123def456abc123def456abc1")
    assert result.status == ReconciliationStatus.PENDING
    assert result.reconciler == "flux"


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git"))
def test_check_reconciliation_status_not_found(mock_run, reconciler):
    result = reconciler.check_reconciliation_status("0000000000000000000000000000000000000000")
    assert result.status == ReconciliationStatus.FAILED


@patch("subprocess.run")
def test_check_reconciliation_with_argocd(mock_run, reconciler):
    mock_run.return_value = MagicMock(returncode=0)
    result = reconciler.check_reconciliation_status(
        "abc123def456abc123def456abc123def456abc1", reconciler="argocd"
    )
    assert result.reconciler == "argocd"


@patch.object(GitOpsReconciler, "_git_add")
@patch.object(GitOpsReconciler, "_git_commit")
@patch.object(GitOpsReconciler, "_get_head_hash", return_value="abc123def456abc123def456abc123def456abc1")
def test_create_multiple_patches(mock_hash, mock_commit, mock_add, reconciler):
    patches = [
        reconciler.generate_replica_patch("app1", "ns1", 3),
        reconciler.generate_replica_patch("app2", "ns2", 5),
        reconciler.generate_image_patch("app1", "ns1", "web", "nginx:latest"),
    ]
    commit = reconciler.create_remediation_commit("inc-006", patches)
    assert len(commit.manifests) == 3
    manifest_dir = Path(reconciler.repo_path) / "manifests" / "inc-006"
    files = list(manifest_dir.iterdir())
    assert len(files) == 3
