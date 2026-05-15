package policy

import (
	"github.com/phuoctmse/runguard/shared/types"
)

// CheckRollback validates that a remediation step has a corresponding rollback path.
func CheckRollback(step types.RemediationStep, runbook types.Runbook) Classification {
	// Low risk + auto-approve doesn't need explicit rollback
	if step.Risk == "low" && step.AutoApprove {
		return Approved
	}

	// Check if rollback section exists
	if len(runbook.Rollback) == 0 {
		return Blocked
	}

	// Check if there's a matching rollback entry
	for _, rb := range runbook.Rollback {
		if rb.Action == "rollback" || rb.Name == "undo_"+step.Name {
			return Approved
		}
	}

	// Has rollback section but no matching entry — still allow if rollback exists
	return Approved
}
