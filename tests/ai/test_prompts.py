"""Tests for the AI prompts module."""

from runguard.backend.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt


class TestSystemPrompt:
    def test_system_prompt_contains_role(self):
        assert "SRE" in SYSTEM_PROMPT

    def test_system_prompt_mentions_json(self):
        assert "JSON" in SYSTEM_PROMPT

    def test_system_prompt_mentions_rollback(self):
        assert "rollback" in SYSTEM_PROMPT.lower()


class TestBuildAnalysisPrompt:
    def test_prompt_contains_incident_id(self):
        prompt = build_analysis_prompt(
            incident_id="inc-abc123",
            namespace="default",
            workload="web-app",
            severity="high",
            raw_alert="PodCrashLooping",
            evidence={},
        )
        assert "inc-abc123" in prompt

    def test_prompt_contains_workload_and_namespace(self):
        prompt = build_analysis_prompt(
            incident_id="inc-1",
            namespace="production",
            workload="payment-svc",
            severity="critical",
            raw_alert="OOMKilled",
            evidence={},
        )
        assert "payment-svc" in prompt
        assert "production" in prompt

    def test_prompt_contains_evidence(self):
        evidence = {
            "pod_logs": {"pod-1": "Error: OOMKilled"},
            "events": [{"reason": "OOMKilling", "message": "Memory exceeded"}],
        }
        prompt = build_analysis_prompt(
            incident_id="inc-1",
            namespace="default",
            workload="web-app",
            severity="high",
            raw_alert="OOM",
            evidence=evidence,
        )
        assert "OOMKilled" in prompt
        assert "OOMKilling" in prompt

    def test_prompt_contains_runbook_title(self):
        prompt = build_analysis_prompt(
            incident_id="inc-1",
            namespace="default",
            workload="web-app",
            severity="high",
            raw_alert="alert",
            evidence={},
            runbook_title="My Runbook",
        )
        assert "My Runbook" in prompt

    def test_prompt_requests_json_output(self):
        prompt = build_analysis_prompt(
            incident_id="inc-1",
            namespace="default",
            workload="web-app",
            severity="high",
            raw_alert="alert",
            evidence={},
        )
        assert "JSON" in prompt or "json" in prompt

    def test_prompt_empty_evidence_says_no_evidence(self):
        prompt = build_analysis_prompt(
            incident_id="inc-1",
            namespace="default",
            workload="web-app",
            severity="high",
            raw_alert="alert",
            evidence={},
        )
        assert "No evidence" in prompt or "no evidence" in prompt


class TestFormatEvidence:
    def test_format_pod_logs(self):
        from runguard.backend.ai.prompts import _format_evidence

        evidence = {"pod_logs": {"pod-1": "CrashLoopBackOff"}}
        result = _format_evidence(evidence)
        assert "pod-1" in result
        assert "CrashLoopBackOff" in result

    def test_format_events(self):
        from runguard.backend.ai.prompts import _format_evidence

        evidence = {"events": [{"reason": "Pulling", "message": "pulling image"}]}
        result = _format_evidence(evidence)
        assert "Pulling" in result
        assert "pulling image" in result

    def test_format_deployment_status(self):
        from runguard.backend.ai.prompts import _format_evidence

        evidence = {
            "deployment_status": {
                "desired_replicas": 3,
                "ready_replicas": 1,
                "available_replicas": 1,
            }
        }
        result = _format_evidence(evidence)
        assert "3" in result
        assert "1" in result

    def test_format_empty_evidence(self):
        from runguard.backend.ai.prompts import _format_evidence

        result = _format_evidence({})
        assert "No evidence" in result
