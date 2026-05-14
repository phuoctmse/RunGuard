package policy

import (
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestBlastRadiusWithinLimit(t *testing.T) {
	policy := types.Policy{
		BlastRadius: types.BlastRadius{
			MaxPodsAffected:       5,
			MaxNamespacesAffected: 1,
		},
	}

	result := CheckBlastRadius(3, 1, policy)
	if result != Approved {
		t.Errorf("result = %v, want Approved", result)
	}
}

func TestBlastRadiusExceedsLimit(t *testing.T) {
	policy := types.Policy{
		BlastRadius: types.BlastRadius{
			MaxPodsAffected: 5,
		},
	}

	result := CheckBlastRadius(10, 1, policy)
	if result != RequiresApproval {
		t.Errorf("result = %v, want RequiresApproval", result)
	}
}

func TestBlastRadiusForbidDelete(t *testing.T) {
	policy := types.Policy{
		BlastRadius: types.BlastRadius{
			ForbidDelete: true,
		},
	}

	action := types.ProposedAction{Action: "delete"}
	result := CheckBlastRadiusAction(action, policy)
	if result != Blocked {
		t.Errorf("result = %v, want Blocked", result)
	}
}

func TestBlastRadiusDeleteAllowed(t *testing.T) {
	policy := types.Policy{
		BlastRadius: types.BlastRadius{
			ForbidDelete: false,
		},
	}

	action := types.ProposedAction{Action: "delete"}
	result := CheckBlastRadiusAction(action, policy)
	if result != Approved {
		t.Errorf("result = %v, want Approved", result)
	}
}
