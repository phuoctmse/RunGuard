"""MCP tool implementations wrapping K8s and AWS operations."""

from typing import Any

import boto3

from runguard.aws.ssm_executor import SSMExecutor
from runguard.backend.evidence.kubernetes import KubernetesEvidenceCollector
from runguard.mcp.models import ToolDefinition, ToolParameter


def get_k8s_pod_logs_tool() -> ToolDefinition:
    """K8s pod logs tool definition."""
    return ToolDefinition(
        name="k8s_pod_logs",
        description="Collect logs from pods matching a workload name in a namespace.",
        parameters=[
            ToolParameter(
                name="workload",
                type="string",
                description="Workload/app name to search pods for",
                required=True,
            ),
            ToolParameter(
                name="tail_lines",
                type="integer",
                description="Number of log lines to retrieve from the end",
                default=100,
            ),
        ],
        required_permissions=["k8s:pods:logs"],
    )


def get_k8s_events_tool() -> ToolDefinition:
    """K8s events tool definition."""
    return ToolDefinition(
        name="k8s_events",
        description="Collect Kubernetes events related to a workload.",
        parameters=[
            ToolParameter(
                name="workload",
                type="string",
                description="Workload name to get events for",
                required=True,
            ),
        ],
        required_permissions=["k8s:events:read"],
    )


def get_k8s_deployment_status_tool() -> ToolDefinition:
    """K8s deployment status tool definition."""
    return ToolDefinition(
        name="k8s_deployment_status",
        description="Get deployment status including replica counts and conditions.",
        parameters=[
            ToolParameter(
                name="workload",
                type="string",
                description="Deployment name",
                required=True,
            ),
        ],
        required_permissions=["k8s:deployments:read"],
    )


def get_k8s_describe_pod_tool() -> ToolDefinition:
    """K8s describe pod tool definition."""
    return ToolDefinition(
        name="k8s_describe_pod",
        description="Describe pod details including status, containers, and events.",
        parameters=[
            ToolParameter(
                name="pod_name",
                type="string",
                description="Pod name to describe",
                required=True,
            ),
        ],
        required_permissions=["k8s:pods:describe"],
    )


def get_cloudwatch_metrics_tool() -> ToolDefinition:
    """CloudWatch metrics tool definition."""
    return ToolDefinition(
        name="cloudwatch_metrics",
        description="Query CloudWatch metrics for a namespace or workload.",
        parameters=[
            ToolParameter(
                name="namespace",
                type="string",
                description="CloudWatch namespace (e.g. AWS/ECS, ContainerInsights)",
                required=True,
            ),
            ToolParameter(
                name="metric_name",
                type="string",
                description="Metric name to query",
                required=True,
            ),
            ToolParameter(
                name="period",
                type="integer",
                description="Aggregation period in seconds",
                default=300,
            ),
            ToolParameter(
                name="hours",
                type="integer",
                description="How many hours of data to retrieve",
                default=1,
            ),
        ],
        required_permissions=["cloudwatch:GetMetricData"],
    )


def get_ssm_trigger_tool() -> ToolDefinition:
    """SSM document trigger tool definition."""
    return ToolDefinition(
        name="ssm_trigger",
        description="Trigger an AWS Systems Manager document on target instances.",
        parameters=[
            ToolParameter(
                name="document_name",
                type="string",
                description="SSM document name",
                required=True,
            ),
            ToolParameter(
                name="targets",
                type="array",
                description="List of target instance IDs",
                required=True,
            ),
        ],
        required_permissions=["ssm:SendCommand"],
    )


def get_all_tool_definitions() -> list[ToolDefinition]:
    """Return all available MCP tool definitions."""
    return [
        get_k8s_pod_logs_tool(),
        get_k8s_events_tool(),
        get_k8s_deployment_status_tool(),
        get_k8s_describe_pod_tool(),
        get_cloudwatch_metrics_tool(),
        get_ssm_trigger_tool(),
    ]


async def execute_k8s_pod_logs(
    arguments: dict[str, Any], namespace: str = "default"
) -> dict[str, Any]:
    """Execute k8s_pod_logs tool."""
    collector = KubernetesEvidenceCollector(namespace=namespace)
    workload = arguments["workload"]
    tail_lines = arguments.get("tail_lines", 100)
    return await collector.collect_pod_logs(workload, tail_lines=tail_lines)


async def execute_k8s_events(
    arguments: dict[str, Any], namespace: str = "default"
) -> list[dict[str, str]]:
    """Execute k8s_events tool."""
    collector = KubernetesEvidenceCollector(namespace=namespace)
    workload = arguments["workload"]
    return await collector.collect_events(workload)


async def execute_k8s_deployment_status(
    arguments: dict[str, Any], namespace: str = "default"
) -> dict[str, object]:
    """Execute k8s_deployment_status tool."""
    collector = KubernetesEvidenceCollector(namespace=namespace)
    workload = arguments["workload"]
    return await collector.collect_deployment_status(workload)


async def execute_k8s_describe_pod(
    arguments: dict[str, Any], namespace: str = "default"
) -> dict[str, Any]:
    """Execute k8s_describe_pod tool."""
    collector = KubernetesEvidenceCollector(namespace=namespace)
    pod_name = arguments["pod_name"]
    try:
        assert collector.core_api is not None
        pod = collector.core_api.read_namespaced_pod(
            name=pod_name, namespace=namespace
        )
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node": pod.spec.node_name,
            "ip": pod.status.pod_ip,
            "containers": [
                {
                    "name": c.name,
                    "image": c.image,
                    "ready": any(
                        cs.name == c.name and cs.ready
                        for cs in (pod.status.container_statuses or [])
                    ),
                }
                for c in pod.spec.containers
            ],
        }
    except Exception as e:
        return {"error": f"Failed to describe pod: {e}"}


async def execute_cloudwatch_metrics(
    arguments: dict[str, Any], region: str = "us-east-1", **kwargs: Any
) -> dict[str, Any]:
    """Execute cloudwatch_metrics tool."""
    from datetime import UTC, datetime, timedelta

    cw = boto3.client("cloudwatch", region_name=region)
    namespace = arguments["namespace"]
    metric_name = arguments["metric_name"]
    period = arguments.get("period", 300)
    hours = arguments.get("hours", 1)

    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=hours)

    try:
        response = cw.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "m1",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": namespace,
                            "MetricName": metric_name,
                        },
                        "Period": period,
                        "Stat": "Average",
                    },
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
        )
        results = response.get("MetricDataResults", [])
        if results:
            return {
                "metric": metric_name,
                "timestamps": [
                    t.isoformat() for t in results[0].get("Timestamps", [])
                ],
                "values": results[0].get("Values", []),
            }
        return {"metric": metric_name, "timestamps": [], "values": []}
    except Exception as e:
        return {"error": f"Failed to query CloudWatch: {e}"}


async def execute_ssm_trigger(
    arguments: dict[str, Any], region: str = "us-east-1", **kwargs: Any
) -> dict[str, Any]:
    """Execute ssm_trigger tool."""
    executor = SSMExecutor(region_name=region)
    document_name = arguments["document_name"]
    targets = arguments["targets"]
    return executor.trigger_document(document_name, targets)


# Type for tool executor functions
ToolExecutor = Any

TOOL_EXECUTORS: dict[str, ToolExecutor] = {
    "k8s_pod_logs": execute_k8s_pod_logs,
    "k8s_events": execute_k8s_events,
    "k8s_deployment_status": execute_k8s_deployment_status,
    "k8s_describe_pod": execute_k8s_describe_pod,
    "cloudwatch_metrics": execute_cloudwatch_metrics,
    "ssm_trigger": execute_ssm_trigger,
}
