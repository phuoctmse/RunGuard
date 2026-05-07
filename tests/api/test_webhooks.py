"""Tests for the Alertmanager webhook endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from runguard.backend.main import app  # noqa: E402

client = TestClient(app)

ALERTMANAGER_PAYLOAD = {
    "alerts": [
        {
            "status": "firing",
            "labels": {
                "alertname": "PodCrashLooping",
                "namespace": "default",
                "pod": "my-app-xxx",
                "severity": "critical",
            },
            "annotations": {
                "summary": "Pod is crash looping",
                "description": "5 restarts in 10 minutes",
            },
        }
    ]
}


class TestWebhookAlertmanager:
    @patch("runguard.backend.api.webhooks.settings")
    def test_webhook_creates_incident(self, mock_settings):
        mock_settings.webhook_secret = "test-secret-123"
        response = client.post(
            "/webhooks/alertmanager",
            json=ALERTMANAGER_PAYLOAD,
            headers={"Authorization": "Bearer test-secret-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["incidents_created"] == 1
        assert len(data["incident_ids"]) == 1

    @patch("runguard.backend.api.webhooks.settings")
    def test_webhook_rejects_invalid_token(self, mock_settings):
        mock_settings.webhook_secret = "test-secret-123"
        response = client.post(
            "/webhooks/alertmanager",
            json=ALERTMANAGER_PAYLOAD,
            headers={"Authorization": "Bearer wrong-secret"},
        )
        assert response.status_code == 401

    @patch("runguard.backend.api.webhooks.settings")
    def test_webhook_rejects_missing_auth(self, mock_settings):
        mock_settings.webhook_secret = "test-secret-123"
        response = client.post(
            "/webhooks/alertmanager",
            json=ALERTMANAGER_PAYLOAD,
        )
        assert response.status_code == 401

    @patch("runguard.backend.api.webhooks.settings")
    def test_webhook_skips_resolved_alerts(self, mock_settings):
        mock_settings.webhook_secret = "test-secret-123"
        payload = {
            "alerts": [
                {
                    "status": "resolved",
                    "labels": {
                        "alertname": "Test",
                        "namespace": "default",
                        "severity": "critical",
                    },
                    "annotations": {"summary": "Resolved"},
                }
            ]
        }
        response = client.post(
            "/webhooks/alertmanager",
            json=payload,
            headers={"Authorization": "Bearer test-secret-123"},
        )
        assert response.status_code == 200
        assert response.json()["incidents_created"] == 0

    @patch("runguard.backend.api.webhooks.settings")
    def test_webhook_returns_incident_ids(self, mock_settings):
        mock_settings.webhook_secret = "test-secret-123"
        response = client.post(
            "/webhooks/alertmanager",
            json=ALERTMANAGER_PAYLOAD,
            headers={"Authorization": "Bearer test-secret-123"},
        )
        data = response.json()
        assert all(inc_id.startswith("inc-") for inc_id in data["incident_ids"])
