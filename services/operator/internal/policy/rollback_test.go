package policy

import (
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestRollbackCheckWithRollback(t *testing.T) {
	runbook := types.Runbook{
		Remediation: []types.RemediationStep{
			{Name: "restart", Action: "restart", Risk: "low"},
		},
		Rollback: []types.RemediationStep{
			{Name: "undo_restart", Action: "rollback", Risk: "low"},
		},
	}

	result := CheckRollback(runbook.Remediation[0], runbook)
	if result != Approved {
		t.Errorf("result = %v, want Approved", result)
	}
}

func TestRollbackCheckMissingRollback(t *testing.T) {
	runbook := types.Runbook{
		Remediation: []types.RemediationStep{
			{Name: "dangerous", Action: "delete", Risk: "high"},
		},
		Rollback: []types.RemediationStep{}, // no rollback
	}

	result := CheckRollback(runbook.Remediation[0], runbook)
	if result != Blocked {
		t.Errorf("result = %v, want Blocked", result)
	}
}

func TestRollbackCheckLowRiskAutoApprove(t *testing.T) {
	runbook := types.Runbook{
		Remediation: []types.RemediationStep{
			{Name: "restart", Action: "restart", Risk: "low", AutoApprove: true},
		},
		Rollback: []types.RemediationStep{
			{Name: "undo", Action: "rollback"},
		},
	}

	result := CheckRollback(runbook.Remediation[0], runbook)
	if result != Approved {
		t.Errorf("result = %v, want Approved", result)
	}
}
