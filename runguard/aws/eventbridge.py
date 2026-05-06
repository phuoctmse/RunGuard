"""EventBridge event intake — parses CloudWatch and Prometheus alerts."""

from typing import Any


class EventBridgeIntake:
    """Parses incoming events from EventBridge and creates incident data."""

    def parse_event(self, event: dict[str, Any]) -> dict[str, Any]:
        if event.get("source") == "aws.cloudwatch":
            return self._parse_cloudwatch(event)
        elif event.get("alerts"):
            return self._parse_prometheus(event)
        return {"source": "unknown", "severity": "medium", "raw_alert": str(event)}

    def _parse_cloudwatch(self, event: dict[str, Any]) -> dict[str, Any]:
        detail = event.get("detail", {})
        alarm_name = detail.get("alarmName", "unknown")
        state = detail.get("state", {})
        reason = state.get("reason", "")
        severity = "high" if state.get("value") == "ALARM" else "medium"
        return {
            "source": "cloudwatch",
            "severity": severity,
            "raw_alert": f"CloudWatch Alarm: {alarm_name} - {reason}",
            "environment": "prod",
            "namespace": "default",
            "workload": alarm_name,
        }

    def _parse_prometheus(self, event: dict[str, Any]) -> dict[str, Any]:
        alerts = event.get("alerts", [])
        if not alerts:
            return {
                "source": "prometheus",
                "severity": "medium",
                "raw_alert": "Empty alert",
            }
        alert = alerts[0]
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        return {
            "source": "prometheus",
            "severity": labels.get("severity", "medium"),
            "raw_alert": annotations.get("summary", labels.get("alertname", "Unknown")),
            "environment": "dev",
            "namespace": labels.get("namespace", "default"),
            "workload": labels.get("pod", labels.get("deployment", "unknown")),
        }
