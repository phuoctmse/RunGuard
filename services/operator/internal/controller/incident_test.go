package controller

import (
	"testing"

	"github.com/phuoctmse/runguard/shared/types"
)

func TestMatchRunbook(t *testing.T) {
	runbooks := []types.Runbook{
		{
			AlertName: "PodCrashLooping",
			Severity:  []string{"critical", "warning"},
		},
		{
			AlertName: "HighMemoryUsage",
			Severity:  []string{"critical"},
		},
	}

	tests := []struct {
		name      string
		incident  types.Incident
		wantMatch bool
		wantName  string
	}{
		{
			name:      "matches exact alert name",
			incident:  types.Incident{AlertName: "PodCrashLooping", Severity: "critical"},
			wantMatch: true,
			wantName:  "PodCrashLooping",
		},
		{
			name:      "matches with warning severity",
			incident:  types.Incident{AlertName: "PodCrashLooping", Severity: "warning"},
			wantMatch: true,
			wantName:  "PodCrashLooping",
		},
		{
			name:      "no match for unknown alert",
			incident:  types.Incident{AlertName: "UnknownAlert", Severity: "critical"},
			wantMatch: false,
		},
		{
			name:      "no match for wrong severity",
			incident:  types.Incident{AlertName: "HighMemoryUsage", Severity: "warning"},
			wantMatch: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rb, matched := MatchRunbook(tt.incident, runbooks)
			if matched != tt.wantMatch {
				t.Errorf("MatchRunbook() matched = %v, want %v", matched, tt.wantMatch)
			}
			if matched && rb.AlertName != tt.wantName {
				t.Errorf("AlertName = %q, want %q", rb.AlertName, tt.wantName)
			}
		})
	}
}

func TestClassifyRisk(t *testing.T) {
	tests := []struct {
		action string
		want   string
	}{
		{"restart", "low"},
		{"scale", "medium"},
		{"rollback", "high"},
		{"delete", "high"},
		{"unknown", "medium"},
	}

	for _, tt := range tests {
		t.Run(tt.action, func(t *testing.T) {
			got := ClassifyRisk(tt.action)
			if got != tt.want {
				t.Errorf("ClassifyRisk(%q) = %q, want %q", tt.action, got, tt.want)
			}
		})
	}
}
