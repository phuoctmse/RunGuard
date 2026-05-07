"""Policy validation engine — validates actions against safety rules."""

from typing import Any

from runguard.backend.models.policy import Policy

MAX_AUTO_APPROVED_PER_INCIDENT = 5


class PolicyEngine:
    """Validates proposed actions against policy constraints."""

    def validate_action(
        self,
        action_name: str,
        policy: Policy,
        namespace: str = "default",
        environment: str = "dev",
        allowed_namespaces: list[str] | None = None,
        iam_permissions: list[str] | None = None,
        auto_approved_count: int = 0,
    ) -> dict[str, Any]:
        """Validate a single action against the policy.

        Evaluation follows spec rules #1 → #9 (first-match).

        Returns: {"status": "approved"|"requires_approval"|"blocked", "reason": "..."}
        """
        # Rule #1: Forbidden action
        for forbidden in policy.forbidden_actions:
            if forbidden.name == action_name:
                return {
                    "status": "blocked",
                    "reason": f"Forbidden: {forbidden.reason}",
                }

        # Rule #2: Not in allowed list
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

        # Rule #3: Namespace outside scope
        scope_namespaces = policy.scope.namespaces
        effective_namespaces = allowed_namespaces or scope_namespaces
        if effective_namespaces and namespace not in effective_namespaces:
            return {
                "status": "blocked",
                "reason": f"Scope violation: namespace '{namespace}' not allowed",
            }

        # Rule #4: IAM permissions insufficient
        # AllowedAction doesn't have required_permissions yet; skip if empty
        # In future, each action can declare required IAM permissions
        if iam_permissions is not None:
            pass

        # Rule #5: Production environment
        if environment == "production":
            return {
                "status": "requires_approval",
                "reason": "Production environment requires approval",
            }

        # Rule #6: Blast radius medium/high
        if allowed_action.blast_radius in ("medium", "high"):
            return {
                "status": "requires_approval",
                "reason": (
                    f"Blast radius '{allowed_action.blast_radius}' requires approval"
                ),
            }

        # Rule #7: No rollback path
        if not allowed_action.rollback_path:
            return {
                "status": "requires_approval",
                "reason": "No rollback path defined",
            }

        # Rule #8: Max auto-approved actions reached
        if auto_approved_count >= MAX_AUTO_APPROVED_PER_INCIDENT:
            return {
                "status": "requires_approval",
                "reason": (
                    f"Auto-approve limit reached "
                    f"({MAX_AUTO_APPROVED_PER_INCIDENT} per incident)"
                ),
            }

        # Rule #9: Low risk + rollback + under limit
        return {"status": "approved", "reason": "Low risk action with rollback path"}

    def validate_plan(
        self,
        action_names: list[str],
        policy: Policy,
        namespace: str = "default",
        environment: str = "dev",
        allowed_namespaces: list[str] | None = None,
        iam_permissions: list[str] | None = None,
        auto_approved_count: int = 0,
    ) -> list[dict[str, Any]]:
        """Validate all actions in a remediation plan."""
        results = []
        running_auto_count = auto_approved_count
        for name in action_names:
            result = self.validate_action(
                name,
                policy,
                namespace,
                environment,
                allowed_namespaces,
                iam_permissions,
                running_auto_count,
            )
            results.append(result)
            if result["status"] == "approved":
                running_auto_count += 1
        return results
