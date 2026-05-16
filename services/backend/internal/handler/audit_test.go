package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
)

func TestGetAuditTrail(t *testing.T) {
	auditStore := audit.NewMemoryAuditStore()
	_ = auditStore.Append(audit.Record{
		IncidentID: "inc-1",
		Type:       audit.RecordTypeIncidentCreated,
		Timestamp:  time.Now(),
		Details:    map[string]string{"namespace": "production"},
	})

	h := NewWithAuditStore(auditStore)
	req := httptest.NewRequest(http.MethodGet, "/api/audit/inc-1", nil)
	w := httptest.NewRecorder()

	h.GetAuditTrail(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}

	var records []audit.Record
	_ = json.NewDecoder(w.Body).Decode(&records)
	if len(records) != 1 {
		t.Errorf("count = %d, want 1", len(records))
	}
}

func TestGetAuditTrailNotFound(t *testing.T) {
	auditStore := audit.NewMemoryAuditStore()
	h := NewWithAuditStore(auditStore)

	req := httptest.NewRequest(http.MethodGet, "/api/audit/nonexistent", nil)
	w := httptest.NewRecorder()

	h.GetAuditTrail(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}

	var records []audit.Record
	_ = json.NewDecoder(w.Body).Decode(&records)
	if len(records) != 0 {
		t.Errorf("count = %d, want 0", len(records))
	}
}

func TestGetAuditTrailMultipleRecords(t *testing.T) {
	auditStore := audit.NewMemoryAuditStore()
	now := time.Now()

	_ = auditStore.Append(audit.Record{IncidentID: "inc-1", Type: audit.RecordTypeIncidentCreated, Timestamp: now})
	_ = auditStore.Append(audit.Record{IncidentID: "inc-1", Type: audit.RecordTypePlanProduced, Timestamp: now.Add(1 * time.Minute)})
	_ = auditStore.Append(audit.Record{IncidentID: "inc-1", Type: audit.RecordTypeActionApproved, Timestamp: now.Add(2 * time.Minute)})
	_ = auditStore.Append(audit.Record{IncidentID: "inc-2", Type: audit.RecordTypeIncidentCreated, Timestamp: now})

	h := NewWithAuditStore(auditStore)
	req := httptest.NewRequest(http.MethodGet, "/api/audit/inc-1", nil)
	w := httptest.NewRecorder()

	h.GetAuditTrail(w, req)

	var records []audit.Record
	_ = json.NewDecoder(w.Body).Decode(&records)
	if len(records) != 3 {
		t.Errorf("count = %d, want 3", len(records))
	}
}
