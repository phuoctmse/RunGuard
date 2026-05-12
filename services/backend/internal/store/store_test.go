package store

import (
	"context"
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestMemoryStoreCreateIncident(t *testing.T) {
	s := NewMemoryStore()
	inc := types.Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "production",
		Workload:  "api-server",
		Phase:     types.PhasePending,
	}

	id, err := s.CreateIncident(context.Background(), inc)
	if err != nil {
		t.Fatalf("CreateIncident failed: %v", err)
	}
	if id == "" {
		t.Error("expected non-empty ID")
	}

	got, err := s.GetIncident(context.Background(), id)
	if err != nil {
		t.Fatalf("GetIncident failed: %v", err)
	}
	if got.AlertName != inc.AlertName {
		t.Errorf("AlertName = %q, want %q", got.AlertName, inc.AlertName)
	}
}

func TestMemoryStoreListIncidents(t *testing.T) {
	s := NewMemoryStore()
	if _, err := s.CreateIncident(context.Background(), types.Incident{AlertName: "a", Phase: types.PhasePending}); err != nil {
		t.Fatalf("setup: %v", err)
	}
	if _, err := s.CreateIncident(context.Background(), types.Incident{AlertName: "b", Phase: types.PhaseResolved}); err != nil {
		t.Fatalf("setup: %v", err)
	}

	all, err := s.ListIncidents(context.Background())
	if err != nil {
		t.Fatalf("ListIncidents failed: %v", err)
	}
	if len(all) != 2 {
		t.Errorf("len = %d, want 2", len(all))
	}
}
