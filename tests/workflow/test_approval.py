"""Tests for human approval workflow."""

import time

import pytest

from runguard.backend.workflow.approval import ApprovalWorkflow


@pytest.fixture
def workflow():
    return ApprovalWorkflow(expiry_seconds=60)


def test_create_approval_request(workflow):
    request_id = workflow.create_request(
        incident_id="inc-001",
        action_name="scale_deployment",
        approver="ops-team",
        reason="Blast radius medium",
    )
    assert request_id is not None
    status = workflow.get_status(request_id)
    assert status["status"] == "pending"


def test_approve_action(workflow):
    request_id = workflow.create_request(
        incident_id="inc-001",
        action_name="scale_deployment",
        approver="ops-team",
        reason="Medium risk",
    )
    result = workflow.approve(request_id, approver="john")
    assert result is True
    status = workflow.get_status(request_id)
    assert status["status"] == "approved"
    assert status["approved_by"] == "john"


def test_reject_action(workflow):
    request_id = workflow.create_request(
        incident_id="inc-001",
        action_name="scale_deployment",
        approver="ops-team",
        reason="Medium risk",
    )
    result = workflow.reject(request_id, rejector="jane", reason="Too risky")
    assert result is True
    status = workflow.get_status(request_id)
    assert status["status"] == "rejected"


def test_cannot_approve_twice(workflow):
    request_id = workflow.create_request(
        incident_id="inc-001",
        action_name="scale_deployment",
        approver="ops-team",
        reason="Medium risk",
    )
    workflow.approve(request_id, approver="john")
    result = workflow.approve(request_id, approver="jane")
    assert result is False


def test_expiry(workflow):
    short_workflow = ApprovalWorkflow(expiry_seconds=0)
    request_id = short_workflow.create_request(
        incident_id="inc-001",
        action_name="scale_deployment",
        approver="ops-team",
        reason="Medium risk",
    )
    time.sleep(0.1)
    status = short_workflow.get_status(request_id)
    assert status["status"] == "expired"
