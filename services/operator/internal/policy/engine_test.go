package policy

import (
	"testing"
	"time"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestEngineValidatePlan(t *testing.T) {
	engine := New()

	policy := types.Policy{
		Scope: types.Scope{
			Namespace: []string{"production"},
			Resources: []string{"deployments", "pods"},
		},
		BlastRadius: types.BlastRadius{
			MaxPodsAffected: 5,
			ForbidDelete:    true,
		},
		Approval: types.ApprovalConfig{
			RequireApprovalFor: []string{"medium", "high"},
		},
		Forbidden: []string{"delete_namespace"},
	}

	runbook := types.Runbook{
		Remediation: []types.RemediationStep{
			{Name: "restart", Action: "restart", Risk: "low"},
			{Name: "scale", Action: "scale", Risk: "medium"},
			{Name: "delete_ns", Action: "delete_namespace", Risk: "high"},
		},
		Rollback: []types.RemediationStep{
			{Name: "undo_restart", Action: "rollback"},
			{Name: "undo_scale", Action: "rollback"},
		},
	}

	results := engine.ValidatePlan(runbook.Remediation, policy, runbook, "production")

	if len(results) != 3 {
		t.Fatalf("results count = %d, want 3", len(results))
	}

	// restart in production → requires_approval (production override)
	if results[0].Classification != RequiresApproval {
		t.Errorf("restart: got %v, want RequiresApproval", results[0].Classification)
	}

	// scale medium → requires_approval
	if results[1].Classification != RequiresApproval {
		t.Errorf("scale: got %v, want RequiresApproval", results[1].Classification)
	}

	// delete_namespace → blocked (forbidden)
	if results[2].Classification != Blocked {
		t.Errorf("delete_ns: got %v, want Blocked", results[2].Classification)
	}
}

func TestEngineCompletesWithin5Seconds(t *testing.T) {
	engine := New()
	policy := types.Policy{
		Scope: types.Scope{Namespace: []string{"production"}},
	}
	runbook := types.Runbook{
		Remediation: make([]types.RemediationStep, 100),
		Rollback:    make([]types.RemediationStep, 100),
	}

	start := time.Now()
	engine.ValidatePlan(runbook.Remediation, policy, runbook, "production")
	elapsed := time.Since(start)

	if elapsed > 5*time.Second {
		t.Errorf("validation took %v, want < 5s", elapsed)
	}
}
