package policy

import (
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestScopeCheckApproved(t *testing.T) {
	policy := types.Policy{
		Scope: types.Scope{
			Namespace: []string{"production", "staging"},
			Resources: []string{"deployments", "pods"},
		},
	}

	action := types.ProposedAction{
		Action: "restart",
		Target: "api-server",
	}

	result := CheckScope(action, "production", policy)
	if result != Approved {
		t.Errorf("result = %v, want Approved", result)
	}
}

func TestScopeCheckBlockedWrongNamespace(t *testing.T) {
	policy := types.Policy{
		Scope: types.Scope{
			Namespace: []string{"production"},
		},
	}

	action := types.ProposedAction{Action: "restart", Target: "api-server"}

	result := CheckScope(action, "kube-system", policy)
	if result != Blocked {
		t.Errorf("result = %v, want Blocked", result)
	}
}

func TestScopeCheckEmptyNamespace(t *testing.T) {
	policy := types.Policy{
		Scope: types.Scope{
			Namespace: []string{}, // empty = allow all
		},
	}

	action := types.ProposedAction{Action: "restart", Target: "api-server"}

	result := CheckScope(action, "any-namespace", policy)
	if result != Approved {
		t.Errorf("result = %v, want Approved (empty scope allows all)", result)
	}
}
