"""Pydantic models for MCP tool definitions and calls."""

from typing import Any

from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Schema for a single tool parameter."""

    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None


class ToolDefinition(BaseModel):
    """Full definition of an MCP tool."""

    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)

    def to_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format for MCP protocol."""
        properties: dict[str, Any] = {}
        required: list[str] = []
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


class ToolCall(BaseModel):
    """An incoming MCP tool call request."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    namespace: str = "default"
    environment: str = "dev"


class ToolResult(BaseModel):
    """Result of an MCP tool execution."""

    tool_name: str
    status: str  # success, blocked, error
    data: Any = None
    error: str | None = None
    policy_decision: dict[str, Any] | None = None
