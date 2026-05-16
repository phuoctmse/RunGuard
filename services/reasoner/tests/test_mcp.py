import pytest

from reasoner.mcp import MCPServer


def test_mcp_tool_definitions():
    server = MCPServer()
    tools = server.list_tools()

    tool_names = [t["name"] for t in tools]
    assert "k8s_pod_logs" in tool_names
    assert "k8s_events" in tool_names
    assert "k8s_deployment_status" in tool_names


def test_mcp_tool_call_with_policy_check():
    server = MCPServer(allowed_namespaces=["production"])

    # Allowed namespace
    result = server.call_tool("k8s_pod_logs", {"namespace": "production", "pod": "api-123"})
    assert result.get("error") is None

    # Blocked namespace
    result = server.call_tool("k8s_pod_logs", {"namespace": "kube-system", "pod": "api-123"})
    assert "error" in result


def test_mcp_tool_not_found():
    server = MCPServer()
    result = server.call_tool("nonexistent_tool", {})
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_mcp_tool_missing_required_params():
    server = MCPServer()
    result = server.call_tool("k8s_pod_logs", {})  # missing namespace and pod
    assert "error" in result