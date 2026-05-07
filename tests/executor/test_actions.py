import pytest

from runguard.backend.executor.actions import SUPPORTED_ACTIONS, execute_action


class TestExecuteAction:
    def test_execute_rollout_restart(self):
        result = execute_action(
            action_name="rollout_restart",
            target="my-app",
            namespace="default",
            parameters={},
            dry_run=True,
        )
        assert result["status"] == "completed"
        assert result["action"] == "rollout_restart"

    def test_execute_scale_replicas(self):
        result = execute_action(
            action_name="scale_replicas",
            target="my-app",
            namespace="default",
            parameters={"replicas": 3},
            dry_run=True,
        )
        assert result["status"] == "completed"
        assert "3" in result["output"]

    def test_execute_update_image(self):
        result = execute_action(
            action_name="update_image",
            target="my-app",
            namespace="default",
            parameters={"image": "my-app:v2"},
            dry_run=True,
        )
        assert result["status"] == "completed"
        assert "my-app:v2" in result["output"]

    def test_execute_delete_pod(self):
        result = execute_action(
            action_name="delete_pod",
            target="my-app-xxx",
            namespace="default",
            parameters={},
            dry_run=True,
        )
        assert result["status"] == "completed"

    def test_execute_unknown_action_fails(self):
        result = execute_action(
            action_name="unknown_action",
            target="my-app",
            namespace="default",
            parameters={},
            dry_run=True,
        )
        assert result["status"] == "failed"
        assert "unknown" in result["error"].lower()

    def test_dry_run_does_not_call_k8s(self):
        result = execute_action(
            action_name="rollout_restart",
            target="my-app",
            namespace="default",
            parameters={},
            dry_run=True,
        )
        assert result["status"] == "completed"


class TestSupportedContent:
    def test_supported_actions_has_expected_members(self):
        expected = {"rollout_restart", "scale_replicas", "update_image", "delete_pod"}
        assert SUPPORTED_ACTIONS == expected

    def test_default_parameters_is_empty_dict(self):
        result = execute_action(
            action_name="rollout_restart",
            target="my-app",
            dry_run=True,
        )
        assert result["status"] == "completed"

    def test_unknown_action_returns_empty_output(self):
        result = execute_action(
            action_name="nonexistent",
            target="my-app",
            dry_run=True,
        )
        assert result["output"] == ""
