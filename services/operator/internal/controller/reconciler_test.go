package controller

import (
	"context"
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestReconcilerProcessIncident(t *testing.T) {
	store := NewMemoryIncidentStore()
	runbooks := []types.Runbook{
		{
			AlertName: "PodCrashLooping",
			Severity:  []string{"critical", "warning"},
			Diagnosis: []types.DiagnosisStep{
				{Name: "check_logs", Command: "echo logs"},
			},
			Remediation: []types.RemediationStep{
				{Name: "restart", Action: "restart", Target: "{{.PodName}}", Risk: "low", AutoApprove: true},
			},
		},
	}

	rec := NewReconciler(store, runbooks, nil)

	inc := types.Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "production",
		Workload:  "api-server-xyz",
		Phase:     types.PhasePending,
	}

	id, err := store.Create(context.Background(), inc)
	if err != nil {
		t.Fatalf("Create failed: %v", err)
	}

	err = rec.Reconcile(context.Background(), id)
	if err != nil {
		t.Fatalf("Reconcile failed: %v", err)
	}

	got, _ := store.Get(context.Background(), id)
	if got.Phase != types.PhaseResolved {
		t.Errorf("Phase = %q, want %q", got.Phase, types.PhaseResolved)
	}
}

func TestReconcilerNoMatchingRunbook(t *testing.T) {
	store := NewMemoryIncidentStore()
	rec := NewReconciler(store, nil, nil)

	inc := types.Incident{
		AlertName: "UnknownAlert",
		Severity:  "critical",
		Phase:     types.PhasePending,
	}

	id, _ := store.Create(context.Background(), inc)
	err := rec.Reconcile(context.Background(), id)
	if err == nil {
		t.Error("expected error for no matching runbook")
	}

	got, _ := store.Get(context.Background(), id)
	if got.Phase != types.PhaseFailed {
		t.Errorf("Phase = %q, want %q", got.Phase, types.PhaseFailed)
	}
}
