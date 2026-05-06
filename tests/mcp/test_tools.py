"""Tests for MCP tool implementations."""

import pytest

from runguard.mcp.models import ToolDefinition
from runguard.mcp.tools import (
    TOOL_EXECUTORS,
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
