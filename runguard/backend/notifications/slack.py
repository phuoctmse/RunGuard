import asyncio
import logging

import httpx

from runguard.backend.notifications.base import NotificationSender

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class SlackNotifier(NotificationSender):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self._last_send_time = 0.0

    async def _send(self, text: str) -> None:
        if not self.webhook_url:
            return

        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_send_time
        if elapsed < 0.1:
            await asyncio.sleep(0.1 - elapsed)

        for attempt in range(_MAX_RETRIES):
            try:
                response = await self.client.post(
                    self.webhook_url, json={"text": text}
                )
                self._last_send_time = asyncio.get_event_loop().time()

                if response.status_code == 429:
                    delay = _BASE_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue

                if response.status_code >= 400:
                    logger.warning(
                        "Slack webhook returned %d: %s",
                        response.status_code, response.text,
                    )
                return
            except Exception as e:
                if attempt < _MAX_RETRIES - 1:
                    delay = _BASE_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.warning("Slack notification failed after retries: %s", e)

    async def send_incident_created(self, incident_id: str, workload: str, severity: str) -> None:
        await self._send(f":red_circle: New incident: {incident_id} — {workload} ({severity})")

    async def send_approval_required(self, incident_id: str, action: str) -> None:
        await self._send(f":warning: Approval needed: {incident_id} — {action}")

    async def send_action_executed(self, incident_id: str, action: str) -> None:
        await self._send(f":white_check_mark: Action executed: {incident_id} — {action}")

    async def send_action_failed(self, incident_id: str, action: str, error: str) -> None:
        await self._send(f":x: Action failed: {incident_id} — {action}: {error}")

    async def send_resolved(self, incident_id: str, summary: str) -> None:
        await self._send(f":large_green_circle: Resolved: {incident_id} — {summary}")
