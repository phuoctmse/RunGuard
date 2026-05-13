package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/phuoctmse/runguard/services/backend/internal/store"
	"github.com/phuoctmse/runguard/shared/types"
)

func TestCreateIncident(t *testing.T) {
	s := store.NewMemoryStore()
	h := NewWithStore(s)

	body := types.Incident{
		AlertName: "PodCrashLooping",
		Severity:  "critical",
		Namespace: "production",
		Workload:  "api-server",
	}
	data, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/api/incidents", bytes.NewReader(data))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	h.CreateIncident(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("status = %d, want %d", w.Code, http.StatusCreated)
	}

	var resp map[string]string
	json.NewDecoder(w.Body).Decode(&resp)
	if resp["id"] == "" {
		t.Error("expected non-empty ID")
	}
}

func TestListIncidents(t *testing.T) {
	s := store.NewMemoryStore()
	s.CreateIncident(nil, types.Incident{AlertName: "a", Phase: types.PhasePending})
	s.CreateIncident(nil, types.Incident{AlertName: "b", Phase: types.PhaseResolved})

	h := NewWithStore(s)
	req := httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
	w := httptest.NewRecorder()

	h.ListIncidents(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}

	var resp []types.Incident
	json.NewDecoder(w.Body).Decode(&resp)
	if len(resp) != 2 {
		t.Errorf("count = %d, want 2", len(resp))
	}
}

func TestGetIncidentNotFound(t *testing.T) {
	s := store.NewMemoryStore()
	h := NewWithStore(s)

	req := httptest.NewRequest(http.MethodGet, "/api/incidents/nonexistent", nil)
	w := httptest.NewRecorder()

	h.GetIncident(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("status = %d, want %d", w.Code, http.StatusNotFound)
	}
}
