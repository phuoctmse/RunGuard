package policy

import (
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestProductionRequiresApproval(t *testing.T) {
	policy := types.Policy{
		Approval: types.ApprovalConfig{
			RequireApprovalFor: []string{"medium", "high"},
		},
	}

	action := types.ProposedAction{Action: "restart", Risk: "low"}
	result := CheckEnvironment(action, "production", policy)
	if result != RequiresApproval {
		t.Errorf("result = %v, want RequiresApproval (production overrides)", result)
	}
}

func TestStagingLowRiskApproved(t *testing.T) {
	policy := types.Policy{
		Approval: types.ApprovalConfig{
			RequireApprovalFor: []string{"medium", "high"},
		},
	}

	action := types.ProposedAction{Action: "restart", Risk: "low"}
	result := CheckEnvironment(action, "staging", policy)
	if result != Approved {
		t.Errorf("result = %v, want Approved", result)
	}
}

func TestForbiddenAction(t *testing.T) {
	policy := types.Policy{
		Forbidden: []string{"delete_namespace", "modify_rbac"},
	}

	action := types.ProposedAction{Action: "delete_namespace"}
	result := CheckForbidden(action, policy)
	if result != Blocked {
		t.Errorf("result = %v, want Blocked", result)
	}
}

func TestAllowedAction(t *testing.T) {
	policy := types.Policy{
		Forbidden: []string{"delete_namespace"},
	}

	action := types.ProposedAction{Action: "restart"}
	result := CheckForbidden(action, policy)
	if result != Approved {
		t.Errorf("result = %v, want Approved", result)
	}
}
