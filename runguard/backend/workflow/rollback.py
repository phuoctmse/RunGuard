"""Rollback executor — runs undo steps in reverse order."""

from typing import Any


class RollbackExecutor:
    """Executes rollback steps in reverse order of original execution."""

    async def execute_rollback(self, rollback_steps: list[str]) -> dict[str, Any]:
        if not rollback_steps:
            return {"status": "completed", "executed": []}

        executed: list[dict[str, Any]] = []
        for step in reversed(rollback_steps):
            try:
                await self._execute_step(step)
                executed.append({"step": step, "status": "success"})
            except Exception as e:
                executed.append({"step": step, "status": "failed", "error": str(e)})
                return {
                    "status": "failed",
                    "executed": executed,
                    "failed_at": step,
                }

        return {"status": "completed", "executed": executed}

    async def _execute_step(self, step: str) -> None:
        """Execute a single rollback step. Override for actual implementation."""
        pass
