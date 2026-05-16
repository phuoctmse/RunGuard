package handler

import (
	"context"
	"testing"
	"time"

	"github.com/phuoctmse/runguard/services/backend/internal/store"
	"github.com/phuoctmse/runguard/shared/types"
)

func TestApprovalTimeout(t *testing.T) {
	s := store.NewMemoryStore()
	id, _ := s.CreateIncident(context.Background(), types.Incident{
		AlertName: "PodCrashLooping",
		Phase:     types.PhaseRequiresApproval,
	})

	h := NewApprovalHandler(s)

	// Start timeout watcher (30 min in prod, but we test with short timeout)
	h.StartApprovalTimeout(id, 100*time.Millisecond)

	// Wait for timeout
	time.Sleep(200 * time.Millisecond)

	inc, _ := s.GetIncident(context.Background(), id)
	if inc.Phase != types.PhaseRejected {
		t.Errorf("Phase = %q, want %q (auto-expired)", inc.Phase, types.PhaseRejected)
	}
}

func TestApprovalTimeoutCancelledOnApprove(t *testing.T) {
	s := store.NewMemoryStore()
	id, _ := s.CreateIncident(context.Background(), types.Incident{
		AlertName: "PodCrashLooping",
		Phase:     types.PhaseRequiresApproval,
	})

	h := NewApprovalHandler(s)
	h.StartApprovalTimeout(id, 1*time.Second)

	// Approve before timeout
	h.Approve(context.Background(), id, "user-1")

	time.Sleep(1500 * time.Millisecond)

	inc, _ := s.GetIncident(context.Background(), id)
	if inc.Phase != types.PhaseExecuting {
		t.Errorf("Phase = %q, want %q (should not be rejected after approval)", inc.Phase, types.PhaseExecuting)
	}
}

func TestApprovalTimeoutDefault30Minutes(t *testing.T) {
	h := NewApprovalHandler(nil)

	if h.defaultTimeout != 30*time.Minute {
		t.Errorf("defaultTimeout = %v, want 30m", h.defaultTimeout)
	}
}
