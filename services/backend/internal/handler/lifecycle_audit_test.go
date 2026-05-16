package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
	"github.com/phuoctmse/runguard/services/backend/internal/store"
	"github.com/phuoctmse/runguard/shared/types"
)

func TestFullLifecycleAudit(t *testing.T) {
	// Set up all components
	store := store.NewMemoryStore()
	auditStore := audit.NewMemoryAuditStore()

	// Mock Slack server
	slackServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer slackServer.Close()

	auditHandler := NewWithAuditStore(auditStore)
	handler := NewFullHandler(store, auditStore, slackServer.URL)

	// 1. Create incident → audit: IncidentCreated
	id, _ := store.CreateIncident(context.Background(), types.Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "production",
		Workload:  "api-server",
		Phase:     types.PhasePending,
	})

	auditStore.Append(audit.Record{
		IncidentID: id,
		Type:       audit.RecordTypeIncidentCreated,
		Timestamp:  time.Now(),
		Details: map[string]string{
			"alert_name": "PodCrashLooping",
			"namespace":  "production",
		},
	})

	// 2. Produce plan → audit: PlanProduced
	auditStore.Append(audit.Record{
		IncidentID: id,
		Type:       audit.RecordTypePlanProduced,
		Timestamp:  time.Now(),
		Details: map[string]string{
			"runbook": "pod-crashloop-runbook",
		},
	})

	// 3. Approve → audit: ActionApproved (handler.Approve() auto-appends)
	_ = handler.Approve(context.Background(), id, "user-1")

	// 4. Execute → audit: ActionExecuted
	auditStore.Append(audit.Record{
		IncidentID: id,
		Type:       audit.RecordTypeActionExecuted,
		Timestamp:  time.Now(),
		Details: map[string]string{
			"action":       "restart",
			"target":       "api-server",
			"rollback_cmd": "kubectl rollout undo deployment/api-server -n production",
		},
	})

	// 5. Verify: GET /audit/{id} returns all records in order
	req := httptest.NewRequest(http.MethodGet, "/api/audit/"+id, nil)
	w := httptest.NewRecorder()
	auditHandler.GetAuditTrail(w, req)

	var records []audit.Record
	json.NewDecoder(w.Body).Decode(&records)

	if len(records) != 4 {
		t.Errorf("audit count = %d, want 4", len(records))
	}

	// Verify chronological order
	for i := 1; i < len(records); i++ {
		if records[i].Timestamp.Before(records[i-1].Timestamp) {
			t.Errorf("records not in chronological order at index %d", i)
		}
	}

	// Verify record types
	expectedTypes := []audit.RecordType{
		audit.RecordTypeIncidentCreated,
		audit.RecordTypePlanProduced,
		audit.RecordTypeActionApproved,
		audit.RecordTypeActionExecuted,
	}
	for i, expected := range expectedTypes {
		if records[i].Type != expected {
			t.Errorf("record[%d].Type = %q, want %q", i, records[i].Type, expected)
		}
	}
}
