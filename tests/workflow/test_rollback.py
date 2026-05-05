"""Tests for rollback executor."""

import pytest

from runguard.backend.workflow.rollback import RollbackExecutor


@pytest.mark.asyncio
async def test_execute_rollback_in_reverse_order():
    executor = RollbackExecutor()
    executed = []

    async def mock_execute(step):
        executed.append(step)

    executor._execute_step = mock_execute

    steps = ["step1", "step2", "step3"]
    await executor.execute_rollback(steps)
    assert executed == ["step3", "step2", "step1"]


@pytest.mark.asyncio
async def test_execute_empty_rollback():
    executor = RollbackExecutor()
    result = await executor.execute_rollback([])
    assert result["status"] == "completed"
