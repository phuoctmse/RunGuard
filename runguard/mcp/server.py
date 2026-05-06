"""MCP server — tool registry with policy enforcement."""

from typing import Any

from runguard.backend.models.policy import Policy
from runguard.backend.policy.engine import PolicyEngine
from runguard.mcp.models import ToolCall, ToolDefinition, ToolResult
from runguard.mcp.tools import TOOL_EXECUTORS, get_all_tool_definitions


class MCPServer:
    """MCP server with tool registry and policy enforcement."""

    def __init__(self, policy_engine: PolicyEngine | None = None) -> None:
        self.policy_engine = policy_engine or PolicyEngine()
        self._tools: dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        for tool_def in get_all_tool_definitions():
            self._tools[tool_def.name] = tool_def

    def register_tool(self, tool_def: ToolDefinition) -> None:
        """Register a custom tool definition."""
        self._tools[tool_def.name] = tool_def

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools with their schemas."""
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a tool definition by name."""
        return self._tools.get(name)

    async def handle_tool_call(
        self,
        call: ToolCall,
        policy: Policy | None = None,
        allowed_namespaces: list[str] | None = None,
    ) -> ToolResult:
        """Handle an MCP tool call with policy enforcement.

        If a policy is provided, validates the tool call against it
        before execution.
        """
        tool_def = self._tools.get(call.tool_name)
        if tool_def is None:
            return ToolResult(
                tool_name=call.tool_name,
                status="error",
                error=f"Unknown tool: {call.tool_name}",
            )

        # Policy enforcement
        if policy is not None:
            decision = self.policy_engine.validate_action(
                action_name=call.tool_name,
                policy=policy,
                namespace=call.namespace,
                environment=call.environment,
                allowed_namespaces=allowed_namespaces,
            )
            if decision["status"] == "blocked":
                return ToolResult(
                    tool_name=call.tool_name,
                    status="blocked",
                    error=decision.get("reason", "Blocked by policy"),
                    policy_decision=decision,
                )

        # Execute the tool
        executor = TOOL_EXECUTORS.get(call.tool_name)
        if executor is None:
            return ToolResult(
                tool_name=call.tool_name,
                status="error",
                error=f"No executor for tool: {call.tool_name}",
            )

        try:
            if call.tool_name.startswith("k8s_"):
                data = await executor(call.arguments, namespace=call.namespace)
            else:
                data = await executor(call.arguments)
            return ToolResult(
                tool_name=call.tool_name,
                status="success",
                data=data,
                policy_decision=(decision if policy is not None else None),
            )
        except Exception as e:
            return ToolResult(
                tool_name=call.tool_name,
                status="error",
                error=str(e),
            )
