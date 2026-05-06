"""Policy validation engine — validates actions against safety rules."""

from typing import Any

from runguard.backend.models.policy import Policy


class PolicyEngine:
    """Validates proposed actions against policy constraints."""

    def validate_action(
        self,
        action_name: str,
        policy: Policy,
        namespace: str = "default",
        environment: str = "dev",
        allowed_namespaces: list[str] | None = None,
    ) -> dict[str, Any]:
        """Validate a single action against the policy.

        Returns: {"status": "approved"|"requires_approval"|"blocked", "reason": "..."}
        """
        for forbidden in policy.forbidden_actions:
            if forbidden.name == action_name:
                return {
                    "status": "blocked",
                    "reason": f"Forbidden: {forbidden.reason}",
                }

        allowed_action = None
        for allowed in policy.allowed_actions:
            if allowed.name == action_name:
                allowed_action = allowed
                break

        if allowed_action is None:
            return {
                "status": "blocked",
                "reason": f"Action '{action_name}' not in allowed list",
            }

        if environment == "production":
            return {
                "status": "requires_approval",
                "reason": "Production environment requires approval",
            }

        if allowed_namespaces and namespace not in allowed_namespaces:
            return {
                "status": "blocked",
                "reason": f"Scope violation: namespace '{namespace}' not allowed",
            }

        if allowed_action.blast_radius in ("medium", "high"):
            return {
                "status": "requires_approval",
                "reason": (
                    f"Blast radius '{allowed_action.blast_radius}' requires approval"
                ),
            }

        if not allowed_action.rollback_path:
            return {
                "status": "requires_approval",
                "reason": "No rollback path defined",
            }

        return {"status": "approved", "reason": "Low risk action with rollback path"}

    def validate_plan(
        self,
        action_names: list[str],
        policy: Policy,
        namespace: str = "default",
        environment: str = "dev",
        allowed_namespaces: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Validate all actions in a remediation plan."""
        return [
            self.validate_action(
                name, policy, namespace, environment, allowed_namespaces
            )
            for name in action_names
        ]
