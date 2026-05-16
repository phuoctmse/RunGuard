import logging
from typing import Any

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    {
        "name": "k8s_pod_logs",
        "description": "Get logs from a Kubernetes pod",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string", "description": "Kubernetes namespace"},
                "pod": {"type": "string", "description": "Pod name"},
                "tail_lines": {
                    "type": "integer",
                    "description": "Number of lines to tail",
                    "default": 100,
                },
            },
            "required": ["namespace", "pod"],
        },
        "permissions": ["k8s:pods:logs"],
    },
    {
        "name": "k8s_events",
        "description": "Get events for a Kubernetes resource",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "field_selector": {"type": "string"},
            },
            "required": ["namespace"],
        },
        "permissions": ["k8s:events:read"],
    },
    {
        "name": "k8s_deployment_status",
        "description": "Get deployment status",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "deployment": {"type": "string"},
            },
            "required": ["namespace", "deployment"],
        },
        "permissions": ["k8s:deployments:read"],
    },
    {
        "name": "k8s_describe",
        "description": "Describe a Kubernetes resource",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "resource_type": {"type": "string"},
                "resource_name": {"type": "string"},
            },
            "required": ["namespace", "resource_type", "resource_name"],
        },
        "permissions": ["k8s:resources:describe"],
    },
    {
        "name": "cloudwatch_metrics",
        "description": "Get CloudWatch metrics for a resource",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "metric_name": {"type": "string"},
                "dimensions": {"type": "object"},
            },
            "required": ["namespace", "metric_name"],
        },
        "permissions": ["aws:cloudwatch:read"],
    },
    {
        "name": "ssm_trigger",
        "description": "Trigger an SSM Automation runbook",
        "parameters": {
            "type": "object",
            "properties": {
                "document_name": {"type": "string"},
                "parameters": {"type": "object"},
            },
            "required": ["document_name"],
        },
        "permissions": ["aws:ssm:trigger"],
    },
]


class MCPServer:
    def __init__(self, allowed_namespaces: list[str] | None = None):
        self.allowed_namespaces = allowed_namespaces or []
        self._tools = {t["name"]: t for t in TOOL_DEFINITIONS}

    def list_tools(self) -> list[dict]:
        return TOOL_DEFINITIONS

    def call_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        # Check tool exists
        tool = self._tools.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        # Validate required parameters
        required = tool["parameters"].get("required", [])
        for param in required:
            if param not in params:
                return {"error": f"Missing required parameter: {param}"}

        # Policy enforcement: check namespace [Req 14.5]
        namespace = params.get("namespace")
        if namespace and self.allowed_namespaces:
            if namespace not in self.allowed_namespaces:
                return {
                    "error": f"Namespace '{namespace}' not allowed by policy",
                    "allowed_namespaces": self.allowed_namespaces,
                }

        # Execute tool (placeholder — real implementation calls K8s/AWS APIs)
        logger.info(f"Executing tool {tool_name} with params {params}")
        return {
            "tool": tool_name,
            "params": params,
            "result": "placeholder_result",
        }
