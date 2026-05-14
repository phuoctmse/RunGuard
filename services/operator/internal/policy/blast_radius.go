package policy

import (
	"github.com/phuoctmse/runguard/shared/types"
)

// CheckBlastRadius validates the blast radius based on pods and namespaces affected.
func CheckBlastRadius(podsAffected, namespacesAffected int, policy types.Policy) Classification {
	br := policy.BlastRadius

	// Check pods limit
	if br.MaxPodsAffected > 0 && podsAffected > br.MaxPodsAffected {
		return RequiresApproval
	}

	// Check namespaces limit
	if br.MaxNamespacesAffected > 0 && namespacesAffected > br.MaxNamespacesAffected {
		return RequiresApproval
	}

	return Approved
}

// CheckBlastRadiusAction validates an action against blast radius rules.
func CheckBlastRadiusAction(action types.ProposedAction, policy types.Policy) Classification {
	if policy.BlastRadius.ForbidDelete && action.Action == "delete" {
		return Blocked
	}
	return Approved
}
