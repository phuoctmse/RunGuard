package policy

import (
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestFailSafePolicyError(t *testing.T) {
	engine := New()

	results := engine.ValidatePlanSafe(nil, types.Policy{}, types.Runbook{}, "production")
	for _, r := range results {
		if r.Classification != Blocked {
			t.Errorf("action %q: got %v, want Blocked on error", r.Action, r.Classification)
		}
	}
}

func TestFailSafeMaxAutoApproved(t *testing.T) {
	engine := New()

	policy := types.Policy{
		Scope: types.Scope{Namespace: []string{"staging"}},
	}
	runbook := types.Runbook{
		Remediation: []types.RemediationStep{
			{Action: "restart", Risk: "low"},
			{Action: "restart", Risk: "low"},
			{Action: "restart", Risk: "low"},
			{Action: "restart", Risk: "low"},
			{Action: "restart", Risk: "low"},
			{Action: "restart", Risk: "low"}, // 6th → should require approval
		},
		Rollback: make([]types.RemediationStep, 6),
	}

	results := engine.ValidatePlanWithLimit(runbook.Remediation, policy, runbook, "staging", 5)

	for i := 0; i < 5; i++ {
		if results[i].Classification != Approved {
			t.Errorf("action %d: got %v, want Approved", i, results[i].Classification)
		}
	}
	if results[5].Classification != RequiresApproval {
		t.Errorf("action 5: got %v, want RequiresApproval", results[5].Classification)
	}
}
