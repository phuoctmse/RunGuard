package controller

import (
	"context"
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

type MockReasoner struct {
	result *ReasonerResult
	err    error
}

func (m *MockReasoner) Analyze(ctx context.Context, alert, namespace string, evidence map[string]string) (*ReasonerResult, error) {
	return m.result, m.err
}

func TestReconcilerWithReasoner(t *testing.T) {
	store := NewMemoryIncidentStore()
	runbooks := []types.Runbook{
		{
			AlertName: "PodCrashLooping",
			Severity:  []string{"critical"},
			Diagnosis: []types.DiagnosisStep{
				{Name: "check_logs", Command: "echo logs"},
			},
			Remediation: []types.RemediationStep{
				{Name: "restart", Action: "restart", Risk: "low", AutoApprove: true},
			},
			Rollback: []types.RemediationStep{
				{Name: "undo", Action: "rollback"},
			},
		},
	}

	mockReasoner := &MockReasoner{
		result: &ReasonerResult{
			RootCause:  "OOMKill",
			Confidence: 0.92,
			Actions:    []string{"increase_memory_limit"},
		},
	}

	exec := NewMockExecutor()
	rec := NewReconcilerWithReasoner(store, runbooks, exec, mockReasoner)

	inc := types.Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "production",
		Workload:  "api-server",
		Phase:     types.PhasePending,
	}

	id, _ := store.Create(context.Background(), inc)
	err := rec.Reconcile(context.Background(), id)
	if err != nil {
		t.Fatalf("Reconcile failed: %v", err)
	}

	got, _ := store.Get(context.Background(), id)
	if got.Phase != types.PhaseResolved {
		t.Errorf("Phase = %q, want %q", got.Phase, types.PhaseResolved)
	}
}

func TestReconcilerReasonerTimeout(t *testing.T) {
	store := NewMemoryIncidentStore()
	runbooks := []types.Runbook{
		{
			AlertName: "PodCrashLooping",
			Severity:  []string{"critical"},
			Remediation: []types.RemediationStep{
				{Name: "restart", Action: "restart", Risk: "low", AutoApprove: true},
			},
			Rollback: []types.RemediationStep{
				{Name: "undo", Action: "rollback"},
			},
		},
	}

	mockReasoner := &MockReasoner{
		err: context.DeadlineExceeded,
	}

	exec := NewMockExecutor()
	rec := NewReconcilerWithReasoner(store, runbooks, exec, mockReasoner)

	inc := types.Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "production",
		Workload:  "api-server",
		Phase:     types.PhasePending,
	}

	id, _ := store.Create(context.Background(), inc)
	err := rec.Reconcile(context.Background(), id)

	// Should proceed with rule-based remediation when reasoner times out
	if err != nil {
		t.Fatalf("Reconcile should not fail on reasoner timeout: %v", err)
	}
}
