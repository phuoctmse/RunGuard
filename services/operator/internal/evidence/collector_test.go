package evidence

import (
	"context"
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestCollectorCollectEvidence(t *testing.T) {
	collector := NewCollector()

	inc := types.Incident{
		AlertName: "PodCrashLooping",
		Namespace: "production",
		Workload:  "api-server-xyz",
	}

	diagnosis := []types.DiagnosisStep{
		{Name: "check_logs", Command: "echo fake logs"},
		{Name: "check_events", Command: "echo fake events"},
	}

	evidence, err := collector.Collect(context.Background(), inc, diagnosis)
	if err != nil {
		t.Fatalf("Collect failed: %v", err)
	}

	if len(evidence) != 2 {
		t.Errorf("evidence count = %d, want 2", len(evidence))
	}

	if evidence["check_logs"] != "fake logs\n" {
		t.Errorf("check_logs = %q, want %q", evidence["check_logs"], "fake logs\n")
	}
}

func TestCollectorEmptyDiagnosis(t *testing.T) {
	collector := NewCollector()
	inc := types.Incident{Namespace: "production"}

	evidence, err := collector.Collect(context.Background(), inc, nil)
	if err != nil {
		t.Fatalf("Collect failed: %v", err)
	}
	if len(evidence) != 0 {
		t.Errorf("evidence count = %d, want 0", len(evidence))
	}
}
