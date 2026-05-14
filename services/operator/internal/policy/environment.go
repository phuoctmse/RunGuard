package policy

import (
	"github.com/phuoctmse/runguard/shared/types"
)

// CheckEnvironment validates an action based on environment rules.
// Production environment overrides: all actions require approval [Req 4.6].
func CheckEnvironment(action types.ProposedAction, environment string, policy types.Policy) Classification {
	// Production environment: all actions require approval regardless of risk
	if environment == "production" {
		return RequiresApproval
	}

	// Check if action risk level requires approval
	for _, level := range policy.Approval.RequireApprovalFor {
		if level == action.Risk {
			return RequiresApproval
		}
	}

	return Approved
}

// CheckForbidden validates an action against the forbidden list.
func CheckForbidden(action types.ProposedAction, policy types.Policy) Classification {
	for _, forbidden := range policy.Forbidden {
		if forbidden == action.Action {
			return Blocked
		}
	}
	return Approved
}
