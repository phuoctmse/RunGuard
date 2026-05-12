package types

import (
	"encoding/json"
	"testing"
)

func TestIncidentJson(t *testing.T) {
	inc := Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "production",
		Workload:  "api-server",
	}

	data, err := json.Marshal(inc)
	if err != nil {
		t.Fatalf("failed to marshal Incident: %v", err)
	}

	var decoded Incident
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("failed to unmarshal Incident: %v", err)
	}

	if decoded.AlertName != inc.AlertName {
		t.Errorf("expected AlertName %q, got %q", inc.AlertName, decoded.AlertName)
	}

	if decoded.Severity != inc.Severity {
		t.Errorf("Severity = %q, want %q", decoded.Severity, inc.Severity)
	}
}

func TestIncidentStatusPhase(t *testing.T) {
	phases := []IncidentPhase{
		PhasePending,
		PhaseAnalyzing,
		PhaseRequiresApproval,
		PhaseExecuting,
		PhaseResolved,
		PhaseFailed,
		PhaseRejected,
	}

	for _, phase := range phases {
		if string(phase) == "" {
			t.Errorf("phase %v has empty string", phase)
		}
	}
}

func TestRunbookJson(t *testing.T) {
	runbook := Runbook{
		AlertName: "PodCrashLooping",
		Severity:  []string{"critical", "warning"},
		Diagnosis: []DiagnosisStep{
			{Name: "check_logs", Command: "kubectl logs {{.Podname}}"},
		},
		Remediation: []RemediationStep{
			{Name: "restart", Action: "restart", Target: "{{.PodName}}", Risk: "low", AutoApprove: true},
		},
	}

	data, err := json.Marshal(runbook)
	if err != nil {
		t.Fatalf("failed to marshal Runbook: %v", err)
	}

	var decoded Runbook
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("failed to unmarshal Runbook: %v", err)
	}

	if len(decoded.Diagnosis) != 1 {
		t.Errorf("Diagnosis len = %d, want 1", len(decoded.Diagnosis))
	}

	if decoded.Remediation[0].AutoApprove != true {
		t.Errorf("AutoApprove = %t, want true", decoded.Remediation[0].AutoApprove)
	}
}

func TestPolicyJson(t *testing.T) {
	pol := Policy{
		Scope: Scope{
			Namespace: []string{"production", "staging"},
			Resources: []string{"deployments", "pods"},
		},
		BlastRadius: BlastRadius{
			MaxPodsAffected:       5,
			MaxNamespacesAffected: 1,
			ForbidDelete:          true,
		},
		Approval: ApprovalConfig{
			RequireApprovalFor: []string{"medium", "high"},
			Approvers:          []string{"sre-team"},
			TimeoutMinutes:     30,
		},
		Forbidden: []string{"delete_namespace", "modify_rbac"},
	}

	data, err := json.Marshal(pol)
	if err != nil {
		t.Fatalf("failed to marshal Policy: %v", err)
	}

	var decoded Policy
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("failed to unmarshal Policy: %v", err)
	}

	if decoded.BlastRadius.MaxPodsAffected != 5 {
		t.Errorf("expected MaxPodsAffected %d, got %d", 5, decoded.BlastRadius.MaxPodsAffected)
	}
}
