from runguard.backend.webhooks.alertmanager import AlertmanagerParser


class TestAlertmanagerParser:
    def setup_method(self):
        self.parser = AlertmanagerParser()

    def test_parse_single_firing_alert(self):
        payload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "HighMemoryUsage",
                        "severity": "critical",
                        "namespace": "production",
                        "pod": "web-server-abc123",
                    },
                    "annotations": {
                        "summary": "Memory usage above 90%",
                        "description": "Pod web-server-abc123 memory usage is 95%",
                    },
                }
            ]
        }
        result = self.parser.parse(payload)
        assert len(result) == 1
        incident = result[0]
        assert incident["source"] == "prometheus"
        assert incident["severity"] == "critical"
        assert incident["namespace"] == "production"
        assert incident["workload"] == "web-server-abc123"
        assert "HighMemoryUsage" in incident["raw_alert"]
        assert "Memory usage above 90%" in incident["raw_alert"]
        assert "Pod web-server-abc123 memory usage is 95%" in incident["raw_alert"]

    def test_resolved_alerts_are_skipped(self):
        payload = {
            "alerts": [
                {
                    "status": "resolved",
                    "labels": {
                        "alertname": "HighMemoryUsage",
                        "severity": "critical",
                        "namespace": "production",
                    },
                    "annotations": {"summary": "Memory usage above 90%"},
                }
            ]
        }
        result = self.parser.parse(payload)
        assert result == []

    def test_parse_multiple_alerts(self):
        payload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "Alert1", "severity": "warning"},
                    "annotations": {"summary": "First alert"},
                },
                {
                    "status": "firing",
                    "labels": {"alertname": "Alert2", "severity": "critical"},
                    "annotations": {"summary": "Second alert"},
                },
                {
                    "status": "firing",
                    "labels": {"alertname": "Alert3", "severity": "info"},
                    "annotations": {"summary": "Third alert"},
                },
            ]
        }
        result = self.parser.parse(payload)
        assert len(result) == 3
        assert result[0]["severity"] == "high"
        assert result[1]["severity"] == "critical"
        assert result[2]["severity"] == "low"

    def test_missing_labels_use_defaults(self):
        payload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "MinimalAlert"},
                    "annotations": {},
                }
            ]
        }
        result = self.parser.parse(payload)
        assert len(result) == 1
        incident = result[0]
        assert incident["namespace"] == "default"
        assert incident["severity"] == "medium"
        assert incident["workload"] == "unknown"
        assert incident["source"] == "prometheus"

    def test_empty_alerts_list_returns_empty(self):
        payload = {"alerts": []}
        result = self.parser.parse(payload)
        assert result == []

    def test_no_alerts_key_returns_empty(self):
        payload = {}
        result = self.parser.parse(payload)
        assert result == []

    def test_no_pod_label_falls_back_to_workload_then_unknown(self):
        # No pod label, no workload label -> "unknown"
        payload_no_workload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "Test", "severity": "info"},
                    "annotations": {},
                }
            ]
        }
        result = self.parser.parse(payload_no_workload)
        assert result[0]["workload"] == "unknown"

        # No pod label, has workload label -> uses workload
        payload_with_workload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "Test",
                        "severity": "info",
                        "workload": "my-deployment",
                    },
                    "annotations": {},
                }
            ]
        }
        result = self.parser.parse(payload_with_workload)
        assert result[0]["workload"] == "my-deployment"

    def test_severity_warning_maps_to_high(self):
        payload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "WarnAlert", "severity": "warning"},
                    "annotations": {"summary": "A warning"},
                }
            ]
        }
        result = self.parser.parse(payload)
        assert result[0]["severity"] == "high"

    def test_raw_alert_contains_summary_and_description(self):
        payload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "DiskFull"},
                    "annotations": {
                        "summary": "Disk is full",
                        "description": "Root filesystem at 98%",
                    },
                }
            ]
        }
        result = self.parser.parse(payload)
        raw_alert = result[0]["raw_alert"]
        assert "[DiskFull]" in raw_alert
        assert "Disk is full" in raw_alert
        assert "Root filesystem at 98%" in raw_alert
        assert "—" in raw_alert  # em dash separator

    def test_raw_alert_without_description(self):
        payload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"alertname": "SimpleAlert"},
                    "annotations": {"summary": "Something happened"},
                }
            ]
        }
        result = self.parser.parse(payload)
        raw_alert = result[0]["raw_alert"]
        assert "[SimpleAlert]" in raw_alert
        assert "Something happened" in raw_alert
        assert "—" not in raw_alert  # no em dash when no description
