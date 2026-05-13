package executor

import (
	"context"
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestExecutorRestart(t *testing.T) {
	executor := New()
	action := types.RemediationStep{
		Action: "restart",
		Target: "api-server-xyz",
	}
	inc := types.Incident{Namespace: "production"}

	err := executor.Execute(context.Background(), action, inc)
	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}
}

func TestExecutorScale(t *testing.T) {
	executor := New()
	action := types.RemediationStep{
		Action: "scale",
		Target: "api-server",
	}
	inc := types.Incident{Namespace: "production"}

	err := executor.Execute(context.Background(), action, inc)
	if err != nil {
		t.Fatalf("Execute failed: %v", err)
	}
}

func TestExecutorUnknownAction(t *testing.T) {
	executor := New()
	action := types.RemediationStep{Action: "unknown"}
	inc := types.Incident{}

	err := executor.Execute(context.Background(), action, inc)
	if err == nil {
		t.Error("expected error for unknown action")
	}
}
