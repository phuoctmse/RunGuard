"""Tests for cost tracker."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from runguard.cost.models import (
    ActionCostEstimate,
    CostSource,
    IncidentCostSummary,
    NamespaceCost,
)
from runguard.cost.tracker import ACTION_COST_ESTIMATES, CostTracker


@pytest.fixture
def tracker():
    return CostTracker(region="us-east-1", opencost_endpoint="")


@pytest.fixture
def tracker_with_opencost():
    return CostTracker(region="us-east-1", opencost_endpoint="http://opencost:9090")


def test_tracker_init(tracker):
    assert tracker.region == "us-east-1"
    assert tracker.opencost_endpoint == ""


def test_tracker_init_with_opencost(tracker_with_opencost):
    assert tracker_with_opencost.opencost_endpoint == "http://opencost:9090"


def test_estimate_action_cost_known(tracker):
    result = tracker.estimate_action_cost("rollout_restart")
    assert isinstance(result, ActionCostEstimate)
    assert result.action_name == "rollout_restart"
    assert result.estimated_cost == 0.01
    assert result.confidence == 0.5


def test_estimate_action_cost_unknown(tracker):
    result = tracker.estimate_action_cost("unknown_action")
    assert result.estimated_cost == 0.01  # default


def test_estimate_action_cost_scale(tracker):
    result = tracker.estimate_action_cost("scale_deployment")
    assert result.estimated_cost == 0.05


@patch("boto3.client")
def test_get_incident_cost_success(mock_boto3, tracker):
    mock_ce = MagicMock()
    mock_boto3.return_value = mock_ce
    mock_ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "Groups": [
                    {
                        "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                        "Metrics": {
                            "UnblendedCost": {"Amount": "1.23", "Unit": "USD"}
                        },
                    }
                ]
            }
        ]
    }
    result = tracker.get_incident_cost("inc-001", namespace="default", hours=24)
    assert isinstance(result, IncidentCostSummary)
    assert result.incident_id == "inc-001"
    assert result.total_cost == 1.23
    assert len(result.cost_entries) == 1
    assert result.cost_entries[0].source == CostSource.AWS_COST_EXPLORER


@patch("boto3.client")
def test_get_incident_cost_api_error(mock_boto3, tracker):
    mock_ce = MagicMock()
    mock_boto3.return_value = mock_ce
    mock_ce.get_cost_and_usage.side_effect = Exception("API error")
    result = tracker.get_incident_cost("inc-002")
    assert result.total_cost == 0.0
    assert len(result.cost_entries) == 0


def test_get_namespace_cost_without_opencost(tracker):
    result = tracker.get_namespace_cost("default")
    assert isinstance(result, NamespaceCost)
    assert result.namespace == "default"
    assert result.total_cost == 0.0


@patch("httpx.get")
def test_get_namespace_cost_with_opencost(mock_get, tracker_with_opencost):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "default": {
                    "cpuCost": 0.50,
                    "ramCost": 0.30,
                    "pvCost": 0.10,
                    "totalCost": 0.90,
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = tracker_with_opencost.get_namespace_cost("default", hours=24)
    assert result.namespace == "default"
    assert result.cpu_cost == 0.50
    assert result.memory_cost == 0.30
    assert result.storage_cost == 0.10
    assert result.total_cost == 0.90


@patch("httpx.get", side_effect=Exception("connection error"))
def test_get_namespace_cost_opencost_error(mock_get, tracker_with_opencost):
    result = tracker_with_opencost.get_namespace_cost("default")
    assert result.total_cost == 0.0


@patch("boto3.client")
def test_get_cost_summary(mock_boto3, tracker):
    mock_ce = MagicMock()
    mock_boto3.return_value = mock_ce
    mock_ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "Groups": [
                    {
                        "Keys": ["EC2"],
                        "Metrics": {"UnblendedCost": {"Amount": "2.00", "Unit": "USD"}},
                    }
                ]
            }
        ]
    }
    result = tracker.get_cost_summary(
        incident_id="inc-003",
        namespace="default",
        action_names=["rollout_restart", "scale_deployment"],
        hours=24,
    )
    assert result.incident_id == "inc-003"
    assert result.total_cost == 2.00
    assert len(result.namespace_costs) == 1
    assert result.estimated_action_cost == pytest.approx(0.06)


def test_action_cost_estimates_coverage():
    """All defined action estimates should be positive."""
    for action, cost in ACTION_COST_ESTIMATES.items():
        assert cost > 0, f"Cost for {action} should be positive"
