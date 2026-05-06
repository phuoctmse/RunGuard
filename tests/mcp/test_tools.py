"""Tests for MCP tool implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runguard.mcp.models import ToolDefinition
from runguard.mcp.tools import (
    TOOL_EXECUTORS,
    execute_cloudwatch_metrics,
    execute_k8s_deployment_status,
    execute_k8s_describe_pod,
    execute_k8s_events,
    execute_k8s_pod_logs,
    execute_ssm_trigger,
    get_all_tool_definitions,
    get_cloudwatch_metrics_tool,
    get_k8s_deployment_status_tool,
    get_k8s_describe_pod_tool,
    get_k8s_events_tool,
    get_k8s_pod_logs_tool,
    get_ssm_trigger_tool,
)


def test_get_all_tool_definitions():
    tools = get_all_tool_definitions()
    assert len(tools) == 6
    names = [t.name for t in tools]
    assert "k8s_pod_logs" in names
    assert "k8s_events" in names
    assert "k8s_deployment_status" in names
    assert "k8s_describe_pod" in names
    assert "cloudwatch_metrics" in names
    assert "ssm_trigger" in names


def test_k8s_pod_logs_tool():
    tool = get_k8s_pod_logs_tool()
    assert isinstance(tool, ToolDefinition)
    assert tool.name == "k8s_pod_logs"
    assert "k8s:pods:logs" in tool.required_permissions
    param_names = [p.name for p in tool.parameters]
    assert "workload" in param_names
    assert "tail_lines" in param_names


def test_k8s_events_tool():
    tool = get_k8s_events_tool()
    assert tool.name == "k8s_events"
    assert "k8s:events:read" in tool.required_permissions


def test_k8s_deployment_status_tool():
    tool = get_k8s_deployment_status_tool()
    assert tool.name == "k8s_deployment_status"
    assert "k8s:deployments:read" in tool.required_permissions


def test_k8s_describe_pod_tool():
    tool = get_k8s_describe_pod_tool()
    assert tool.name == "k8s_describe_pod"
    assert "k8s:pods:describe" in tool.required_permissions


def test_cloudwatch_metrics_tool():
    tool = get_cloudwatch_metrics_tool()
    assert tool.name == "cloudwatch_metrics"
    assert "cloudwatch:GetMetricData" in tool.required_permissions
    param_names = [p.name for p in tool.parameters]
    assert "namespace" in param_names
    assert "metric_name" in param_names


def test_ssm_trigger_tool():
    tool = get_ssm_trigger_tool()
    assert tool.name == "ssm_trigger"
    assert "ssm:SendCommand" in tool.required_permissions
    param_names = [p.name for p in tool.parameters]
    assert "document_name" in param_names
    assert "targets" in param_names


def test_tool_executors_map():
    assert len(TOOL_EXECUTORS) == 6
    assert "k8s_pod_logs" in TOOL_EXECUTORS
    assert "k8s_events" in TOOL_EXECUTORS
    assert "k8s_deployment_status" in TOOL_EXECUTORS
    assert "k8s_describe_pod" in TOOL_EXECUTORS
    assert "cloudwatch_metrics" in TOOL_EXECUTORS
    assert "ssm_trigger" in TOOL_EXECUTORS


def test_all_tools_have_schemas():
    for tool in get_all_tool_definitions():
        schema = tool.to_schema()
        assert "name" in schema
        assert "description" in schema
        assert "inputSchema" in schema
        assert schema["inputSchema"]["type"] == "object"


@pytest.mark.asyncio
@patch("runguard.mcp.tools.KubernetesEvidenceCollector")
async def test_execute_k8s_pod_logs(mock_collector_cls):
    mock_collector = MagicMock()
    mock_collector.collect_pod_logs = AsyncMock(return_value={"pod-1": "logs"})
    mock_collector_cls.return_value = mock_collector
    result = await execute_k8s_pod_logs({"workload": "my-app", "tail_lines": 50})
    assert result == {"pod-1": "logs"}
    mock_collector.collect_pod_logs.assert_called_once_with("my-app", tail_lines=50)


@pytest.mark.asyncio
@patch("runguard.mcp.tools.KubernetesEvidenceCollector")
async def test_execute_k8s_events(mock_collector_cls):
    mock_collector = MagicMock()
    mock_collector.collect_events = AsyncMock(return_value=[{"reason": "test"}])
    mock_collector_cls.return_value = mock_collector
    result = await execute_k8s_events({"workload": "my-app"})
    assert result == [{"reason": "test"}]


@pytest.mark.asyncio
@patch("runguard.mcp.tools.KubernetesEvidenceCollector")
async def test_execute_k8s_deployment_status(mock_collector_cls):
    mock_collector = MagicMock()
    mock_collector.collect_deployment_status = AsyncMock(
        return_value={"name": "my-app", "ready_replicas": 3}
    )
    mock_collector_cls.return_value = mock_collector
    result = await execute_k8s_deployment_status({"workload": "my-app"})
    assert result["name"] == "my-app"


@pytest.mark.asyncio
@patch("runguard.mcp.tools.KubernetesEvidenceCollector")
async def test_execute_k8s_describe_pod(mock_collector_cls):
    mock_collector = MagicMock()
    mock_pod = MagicMock()
    mock_pod.metadata.name = "pod-1"
    mock_pod.metadata.namespace = "default"
    mock_pod.status.phase = "Running"
    mock_pod.status.pod_ip = "10.0.0.1"
    mock_pod.status.container_statuses = [MagicMock(name="web", ready=True)]
    mock_pod.spec.node_name = "node-1"
    mock_pod.spec.containers = [MagicMock(name="web", image="nginx:latest")]
    mock_collector.core_api = MagicMock()
    mock_collector.core_api.read_namespaced_pod.return_value = mock_pod
    mock_collector_cls.return_value = mock_collector
    result = await execute_k8s_describe_pod({"pod_name": "pod-1"})
    assert result["name"] == "pod-1"
    assert result["status"] == "Running"


@pytest.mark.asyncio
@patch("runguard.mcp.tools.KubernetesEvidenceCollector")
async def test_execute_k8s_describe_pod_error(mock_collector_cls):
    mock_collector = MagicMock()
    mock_collector.core_api = MagicMock()
    mock_collector.core_api.read_namespaced_pod.side_effect = Exception("not found")
    mock_collector_cls.return_value = mock_collector
    result = await execute_k8s_describe_pod({"pod_name": "missing"})
    assert "error" in result


@pytest.mark.asyncio
@patch("boto3.client")
async def test_execute_cloudwatch_metrics(mock_boto3):
    mock_cw = MagicMock()
    mock_boto3.return_value = mock_cw
    from datetime import datetime

    mock_cw.get_metric_data.return_value = {
        "MetricDataResults": [
            {
                "Timestamps": [datetime(2024, 1, 1)],
                "Values": [42.0],
            }
        ]
    }
    result = await execute_cloudwatch_metrics(
        {"namespace": "AWS/ECS", "metric_name": "CPUUtilization"}
    )
    assert result["metric"] == "CPUUtilization"
    assert result["values"] == [42.0]


@pytest.mark.asyncio
@patch("boto3.client")
async def test_execute_cloudwatch_metrics_error(mock_boto3):
    mock_cw = MagicMock()
    mock_boto3.return_value = mock_cw
    mock_cw.get_metric_data.side_effect = Exception("api error")
    result = await execute_cloudwatch_metrics(
        {"namespace": "AWS/ECS", "metric_name": "CPU"}
    )
    assert "error" in result


@pytest.mark.asyncio
@patch("runguard.mcp.tools.SSMExecutor")
async def test_execute_ssm_trigger(mock_ssm_cls):
    mock_ssm = MagicMock()
    mock_ssm.trigger_document.return_value = {
        "status": "success",
        "execution_id": "cmd-123",
    }
    mock_ssm_cls.return_value = mock_ssm
    result = await execute_ssm_trigger(
        {"document_name": "test-doc", "targets": ["i-123"]}
    )
    assert result["status"] == "success"
    assert result["execution_id"] == "cmd-123"
