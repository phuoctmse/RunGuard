from typing import Any

from runguard.backend.webhooks.base import BaseWebhookParser

_SEVERITY_MAP = {
    "critical": "critical",
    "warning": "high",
    "info": "low",
    "none": "low",
}


class AlertmanagerParser(BaseWebhookParser):
    """Parse Alertmanager webhook payloads into incident-ready dicts."""

    def parse(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract firing alerts from an Alertmanager webhook payload."""
        incidents: list[dict[str, Any]] = []
        for alert in payload.get("alerts", []):
            if alert.get("status") != "firing":
                continue
            incidents.append(self._parse_alert(alert))
        return incidents

    def _parse_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        """Normalize a single Alertmanager alert into an incident dict."""
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        raw_severity = labels.get("severity", "medium").lower()
        severity = _SEVERITY_MAP.get(raw_severity, "medium")
        summary = annotations.get("summary", "")
        description = annotations.get("description", "")
        alertname = labels.get("alertname", "Unknown")
        raw_alert = f"[{alertname}] {summary}"
        if description:
            raw_alert += f" — {description}"
        return {
            "source": "prometheus",
            "severity": severity,
            "namespace": labels.get("namespace", "default"),
            "workload": labels.get("pod", labels.get("workload", "unknown")),
            "raw_alert": raw_alert,
        }
