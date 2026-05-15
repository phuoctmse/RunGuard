package policy

import (
	"github.com/phuoctmse/runguard/shared/types"
)

// CheckScope validates an action against the policy's namespace and resource scope.
func CheckScope(action types.ProposedAction, namespace string, policy types.Policy) Classification {
	// Empty scope = allow all
	if len(policy.Scope.Namespace) == 0 {
		return Approved
	}

	// Check namespace
	allowed := false
	for _, ns := range policy.Scope.Namespace {
		if ns == namespace {
			allowed = true
			break
		}
	}

	if !allowed {
		return Blocked
	}

	return Approved
}
