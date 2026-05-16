package executor

import (
	"context"
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestRollbackOnFailure(t *testing.T) {
	exec := NewWithMode(false) // not dry-run

	actions := []types.RemediationStep{
		{Name: "restart", Action: "restart", Target: "api-server"},
		{Name: "scale", Action: "scale", Target: "api-server"},
	}
	rollbackSteps := []types.RemediationStep{
		{Name: "undo_restart", Action: "rollback", Target: "api-server"},
		{Name: "undo_scale", Action: "rollback", Target: "api-server"},
	}

	exec.SetFailAction("scale")

	err := exec.ExecuteWithRollback(context.Background(), actions, rollbackSteps, types.Incident{Namespace: "production"})
	if err == nil {
		t.Error("expected error from failed scale")
	}

	if len(exec.RollbackLog) != 2 {
		t.Errorf("rollback count = %d, want 2", len(exec.RollbackLog))
	}
	// Reverse order: undo_scale first, then undo_restart
	if exec.RollbackLog[0] != "undo_scale" {
		t.Errorf("first rollback = %q, want %q", exec.RollbackLog[0], "undo_scale")
	}
}

func TestRollbackNotCalledOnSuccess(t *testing.T) {
	exec := NewWithMode(false)

	actions := []types.RemediationStep{
		{Name: "restart", Action: "restart", Target: "api-server"},
	}
	rollbackSteps := []types.RemediationStep{
		{Name: "undo_restart", Action: "rollback", Target: "api-server"},
	}

	err := exec.ExecuteWithRollback(context.Background(), actions, rollbackSteps, types.Incident{Namespace: "production"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(exec.RollbackLog) != 0 {
		t.Errorf("rollback count = %d, want 0 (no failure)", len(exec.RollbackLog))
	}
}

func TestRollbackReverseOrder(t *testing.T) {
	exec := NewWithMode(false)

	actions := []types.RemediationStep{
		{Name: "step1", Action: "restart", Target: "a"},
		{Name: "step2", Action: "scale", Target: "b"},
		{Name: "step3", Action: "deploy", Target: "c"},
	}
	rollbackSteps := []types.RemediationStep{
		{Name: "undo_step1", Action: "rollback", Target: "a"},
		{Name: "undo_step2", Action: "rollback", Target: "b"},
		{Name: "undo_step3", Action: "rollback", Target: "c"},
	}

	exec.SetFailAction("deploy")

	_ = exec.ExecuteWithRollback(context.Background(), actions, rollbackSteps, types.Incident{})

	expected := []string{"undo_step3", "undo_step2", "undo_step1"}
	if len(exec.RollbackLog) != len(expected) {
		t.Fatalf("rollback count = %d, want %d", len(exec.RollbackLog), len(expected))
	}
	for i, name := range expected {
		if exec.RollbackLog[i] != name {
			t.Errorf("rollback[%d] = %q, want %q", i, exec.RollbackLog[i], name)
		}
	}
}
