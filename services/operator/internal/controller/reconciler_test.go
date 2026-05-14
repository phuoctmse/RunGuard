package controller

import (
	"context"
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestReconcilerWithPolicyEngine(t *testing.T) {
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

	policy := types.Policy{
		Scope: types.Scope{
			Namespace: []string{"production"},
		},
	}

	exec := NewMockExecutor()
	rec := NewReconcilerWithPolicy(store, runbooks, exec, policy)

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
	if got.Phase != types.PhaseRequiresApproval {
		t.Errorf("Phase = %q, want %q", got.Phase, types.PhaseRequiresApproval)
	}
}

func TestReconcilerBlocksOutsideScope(t *testing.T) {
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

	policy := types.Policy{
		Scope: types.Scope{Namespace: []string{"production"}},
	}

	exec := NewMockExecutor()
	rec := NewReconcilerWithPolicy(store, runbooks, exec, policy)

	inc := types.Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "kube-system", // outside scope
		Phase:     types.PhasePending,
	}

	id, _ := store.Create(context.Background(), inc)
	err := rec.Reconcile(context.Background(), id)
	if err == nil {
		t.Error("expected error for action outside scope")
	}

	got, _ := store.Get(context.Background(), id)
	if got.Phase != types.PhaseFailed {
		t.Errorf("Phase = %q, want %q", got.Phase, types.PhaseFailed)
	}
}
