import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from runguard.backend.notifications.slack import SlackNotifier


@pytest.fixture
def notifier():
    return SlackNotifier(webhook_url="https://hooks.slack.com/test")


@pytest.mark.asyncio
async def test_send_incident_created(notifier):
    with patch.object(notifier.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200)
        await notifier.send_incident_created("inc-001", "my-app", "critical")
    mock_post.assert_called_once()
    body = mock_post.call_args.kwargs["json"]["text"]
    assert "inc-001" in body
    assert "critical" in body


@pytest.mark.asyncio
async def test_send_approval_required(notifier):
    with patch.object(notifier.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200)
        await notifier.send_approval_required("inc-002", "rollout_restart")
    body = mock_post.call_args.kwargs["json"]["text"]
    assert "inc-002" in body


@pytest.mark.asyncio
async def test_send_action_executed(notifier):
    with patch.object(notifier.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200)
        await notifier.send_action_executed("inc-003", "scale_replicas")
    body = mock_post.call_args.kwargs["json"]["text"]
    assert "inc-003" in body


@pytest.mark.asyncio
async def test_send_action_failed(notifier):
    with patch.object(notifier.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200)
        await notifier.send_action_failed("inc-004", "rollout_restart", "not found")
    body = mock_post.call_args.kwargs["json"]["text"]
    assert "not found" in body


@pytest.mark.asyncio
async def test_send_resolved(notifier):
    with patch.object(notifier.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200)
        await notifier.send_resolved("inc-005", "Fixed by restart")
    body = mock_post.call_args.kwargs["json"]["text"]
    assert "inc-005" in body


@pytest.mark.asyncio
async def test_rate_limit_retry_on_429(notifier):
    call_count = [0]

    async def mock_post(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] < 3:
            return httpx.Response(429, json={"error": "rate_limited"})
        return httpx.Response(200)

    with patch.object(notifier.client, "post", side_effect=mock_post):
        await notifier.send_incident_created("inc-001", "my-app", "high")
    assert call_count[0] == 3


@pytest.mark.asyncio
async def test_graceful_failure_does_not_raise(notifier):
    with patch.object(
        notifier.client, "post", new_callable=AsyncMock, side_effect=Exception("network error")
    ):
        await notifier.send_incident_created("inc-001", "my-app", "high")


@pytest.mark.asyncio
async def test_noop_when_no_webhook_url():
    notifier = SlackNotifier(webhook_url="")
    await notifier.send_incident_created("inc-001", "my-app", "high")
