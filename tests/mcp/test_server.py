"""Tests for MCP server — tool registration and policy enforcement."""

import pytest

from runguard.backend.models.policy import AllowedAction, ForbiddenAction, Policy
from runguard.backend.policy.engine import PolicyEngine
from runguard.mcp.models import ToolCall, ToolDefinition, ToolParameter
from runguard.mcp.server import MCPServer


@pytest.fixture
def server():
    return MCPServer()


@pytest.fixture
def policy():
    return Policy(
        id="pol-001",
        runbook_id="rb-001",
        allowed_actions=[
            AllowedAction(
                name="k8s_pod_logs",
                blast_radius="low",
                requires_approval=False,
                rollback_path=["none"],
            ),
            AllowedAction(
                name="k8s_events",
                blast_radius="low",
                requires_approval=False,
                rollback_path=["none"],
            ),
        ],
        forbidden_actions=[
            ForbiddenAction(name="ssm_trigger", reason="AWS actions forbidden in dev"),
        ],
    )


def test_server_has_default_tools(server):
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "k8s_pod_logs" in names
    assert "k8s_events" in names
    assert "k8s_deployment_status" in names
    assert "k8s_describe_pod" in names
    assert "cloudwatch_metrics" in names
    assert "ssm_trigger" in names


def test_server_tool_schemas_have_required_fields(server):
    tools = server.list_tools()
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema


def test_register_custom_tool(server):
    tool = ToolDefinition(
        name="custom_tool",
        description="A custom tool",
        parameters=[
            ToolParameter(name="arg1", type="string", description="An arg", required=True)
        ],
    )
    server.register_tool(tool)
    assert server.get_tool("custom_tool") is not None


def test_get_tool_returns_none_for_unknown(server):
    assert server.get_tool("nonexistent") is None


@pytest.mark.asyncio
async def test_handle_unknown_tool_returns_error(server):
    call = ToolCall(tool_name="nonexistent_tool")
    result = await server.handle_tool_call(call)
    assert result.status == "error"
    assert "Unknown tool" in result.error


@pytest.mark.asyncio
async def test_handle_blocked_tool_call(server, policy):
    call = ToolCall(
        tool_name="ssm_trigger",
        arguments={"document_name": "test", "targets": ["i-123"]},
        namespace="default",
        environment="dev",
    )
    result = await server.handle_tool_call(call, policy=policy)
    assert result.status == "blocked"
    assert "forbidden" in result.error.lower()


@pytest.mark.asyncio
async def test_handle_allowed_tool_call_with_policy(server, policy):
    call = ToolCall(
        tool_name="k8s_events",
        arguments={"workload": "my-app"},
        namespace="default",
        environment="dev",
    )
    # Will fail on actual K8s call but policy should pass
    result = await server.handle_tool_call(call, policy=policy)
    # Should not be blocked — may be error if no K8s cluster
    assert result.status in ("success", "error")
    assert result.status != "blocked"


@pytest.mark.asyncio
async def test_handle_tool_call_without_policy(server):
    call = ToolCall(
        tool_name="k8s_events",
        arguments={"workload": "my-app"},
    )
    result = await server.handle_tool_call(call)
    # Without policy, should attempt execution (may error without K8s)
    assert result.status in ("success", "error")


def test_tool_definition_to_schema():
    tool = ToolDefinition(
        name="test_tool",
        description="Test",
        parameters=[
            ToolParameter(name="arg1", type="string", description="An arg", required=True),
            ToolParameter(name="arg2", type="integer", description="Optional arg", default=10),
        ],
    )
    schema = tool.to_schema()
    assert schema["name"] == "test_tool"
    assert schema["inputSchema"]["type"] == "object"
    assert "arg1" in schema["inputSchema"]["required"]
    assert "arg2" not in schema["inputSchema"]["required"]
    assert schema["inputSchema"]["properties"]["arg2"]["default"] == 10
