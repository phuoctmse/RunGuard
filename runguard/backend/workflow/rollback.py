"""Rollback executor — runs undo steps in reverse order."""


class RollbackExecutor:
    """Executes rollback steps in reverse order of original execution."""

    async def execute_rollback(self, rollback_steps: list[str]) -> dict:
        if not rollback_steps:
            return {"status": "completed", "executed": []}

        executed = []
        for step in reversed(rollback_steps):
            try:
                await self._execute_step(step)
                executed.append({"step": step, "status": "success"})
            except Exception as e:
                executed.append({"step": step, "status": "failed", "error": str(e)})
                return {"status": "failed", "executed": executed, "failed_at": step}

        return {"status": "completed", "executed": executed}

    async def _execute_step(self, step: str):
        """Execute a single rollback step. Override for actual implementation."""
        pass
