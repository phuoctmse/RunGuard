"""Tests for EventBridge event intake."""

import pytest

from runguard.aws.eventbridge import EventBridgeIntake


def test_parse_cloudwatch_alarm():
    intake = EventBridgeIntake()
    event = {
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "detail": {
            "alarmName": "HighCPUAlarm",
            "state": {
                "value": "ALARM",
                "reason": "CPU utilization exceeded 80%",
            },
            "configuration": {
                "metrics": [{"metric": {"name": "CPUUtilization"}}]
            },
        },
    }
    result = intake.parse_event(event)
    assert result["source"] == "cloudwatch"
    assert result["severity"] == "high"
    assert "HighCPUAlarm" in result["raw_alert"]


def test_parse_prometheus_webhook():
    intake = EventBridgeIntake()
    event = {
        "receiver": "runguard",
        "alerts": [
            {
                "labels": {
                    "alertname": "PodCrashLoop",
                    "severity": "critical",
                },
                "annotations": {"summary": "Pod is crash looping"},
            }
        ],
    }
    result = intake.parse_event(event)
    assert result["source"] == "prometheus"
    assert result["severity"] == "critical"


def test_parse_unknown_event():
    intake = EventBridgeIntake()
    result = intake.parse_event({"unknown": "event"})
    assert result["source"] == "unknown"
