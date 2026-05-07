import logging
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_ACTIONS = {
    "rollout_restart",
    "scale_replicas",
    "update_image",
    "delete_pod",
}


def execute_action(
    action_name: str,
    target: str,
    namespace: str = "default",
    parameters: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute a single remediation action.

    Returns dict with: action, status, output (or error).
    """
    params = parameters or {}

    if action_name not in SUPPORTED_ACTIONS:
        return {
            "action": action_name,
            "status": "failed",
            "error": f"Unknown action: {action_name}",
            "output": "",
        }

    if dry_run:
        return _dry_run_result(action_name, target, namespace, params)

    return _execute(action_name, target, namespace, params)


def _dry_run_result(
    action_name: str, target: str, namespace: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Return a simulated result without touching the cluster."""
    descriptions = {
        "rollout_restart": f"[DRY RUN] Would restart rollout {target}",
        "scale_replicas": (
            f"[DRY RUN] Would scale {target} to {params.get('replicas', '?')} replicas"
        ),
        "update_image": (
            f"[DRY RUN] Would update {target} image to {params.get('image', '?')}"
        ),
        "delete_pod": f"[DRY RUN] Would delete pod {target}",
    }
    return {
        "action": action_name,
        "status": "completed",
        "output": descriptions.get(action_name, f"[DRY RUN] {action_name}"),
    }


def _execute(
    action_name: str, target: str, namespace: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Execute the action against the real cluster via K8sClient."""
    from runguard.backend.executor.k8s_client import K8sClient

    try:
        k8s = K8sClient()
        handlers: dict[str, callable] = {
            "rollout_restart": lambda: k8s.rollout_restart(target, namespace),
            "scale_replicas": lambda: k8s.scale_replicas(
                target, params.get("replicas", 1), namespace
            ),
            "update_image": lambda: k8s.update_image(
                target, params.get("image", ""), namespace
            ),
            "delete_pod": lambda: k8s.delete_pod(target, namespace),
        }
        result = handlers[action_name]()
        return {
            "action": action_name,
            "status": "completed",
            "output": str(result),
            "error": "",
        }
    except Exception as e:
        logger.error("Action %s failed on %s: %s", action_name, target, e)
        return {
            "action": action_name,
            "status": "failed",
            "output": "",
            "error": str(e),
        }
