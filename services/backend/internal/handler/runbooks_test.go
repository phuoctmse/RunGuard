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

func TestCreateRunbook(t *testing.T) {
	s := store.NewMemoryStore()
	h := NewWithStore(s)

	rb := types.Runbook{
		AlertName: "PodCrashLooping",
		Severity:  []string{"critical"},
		Diagnosis: []types.DiagnosisStep{
			{Name: "check_logs", Command: "kubectl logs {{.PodName}}"},
		},
		Remediation: []types.RemediationStep{
			{Name: "restart", Action: "restart", Target: "{{.PodName}}", Risk: "low", AutoApprove: true},
		},
	}
	data, _ := json.Marshal(rb)

	req := httptest.NewRequest(http.MethodPost, "/api/runbooks", bytes.NewReader(data))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	h.CreateRunbook(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("status = %d, want %d", w.Code, http.StatusCreated)
	}
}

func TestListRunbooks(t *testing.T) {
	s := store.NewMemoryStore()
	h := NewWithStore(s)

	// Create runbooks via handler
	h.runbookStore.CreateRunbook(nil, types.Runbook{AlertName: "a"})
	h.runbookStore.CreateRunbook(nil, types.Runbook{AlertName: "b"})

	req := httptest.NewRequest(http.MethodGet, "/api/runbooks", nil)
	w := httptest.NewRecorder()

	h.ListRunbooks(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}

	var resp []types.Runbook
	json.NewDecoder(w.Body).Decode(&resp)
	if len(resp) != 2 {
		t.Errorf("count = %d, want 2", len(resp))
	}
}
