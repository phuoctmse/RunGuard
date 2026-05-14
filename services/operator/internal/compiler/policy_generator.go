package compiler

import (
	"github.com/phuoctmse/runguard/shared/types"
)

// GeneratePolicy converts a ParsedRunbook into a Policy.
func GeneratePolicy(rb *ParsedRunbook) types.Policy {
	policy := types.Policy{
		Scope: types.Scope{
			Namespace: rb.Scope.Namespaces,
			Resources: rb.Scope.Resources,
		},
		Forbidden: rb.Forbidden,
	}

	// Set blast radius defaults based on risk levels
	maxRisk := "low"
	for _, step := range rb.Remediation {
		if step.Risk == "high" {
			maxRisk = "high"
		} else if step.Risk == "medium" && maxRisk != "high" {
			maxRisk = "medium"
		}
	}

	switch maxRisk {
	case "high":
		policy.BlastRadius = types.BlastRadius{
			MaxPodsAffected:       3,
			MaxNamespacesAffected: 1,
			ForbidDelete:          true,
		}
	case "medium":
		policy.BlastRadius = types.BlastRadius{
			MaxPodsAffected:       5,
			MaxNamespacesAffected: 1,
			ForbidDelete:          false,
		}
	default:
		policy.BlastRadius = types.BlastRadius{
			MaxPodsAffected:       10,
			MaxNamespacesAffected: 2,
			ForbidDelete:          false,
		}
	}

	// Set approval config based on severity
	hasHighRisk := false
	for _, step := range rb.Remediation {
		if step.Risk == "high" || step.Risk == "medium" {
			hasHighRisk = true
			break
		}
	}

	if hasHighRisk {
		policy.Approval = types.ApprovalConfig{
			RequireApprovalFor: []string{"medium", "high"},
			TimeoutMinutes:     30,
		}
	} else {
		policy.Approval = types.ApprovalConfig{
			RequireApprovalFor: []string{"high"},
			TimeoutMinutes:     30,
		}
	}

	return policy
}
