package handler

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/phuoctmse/runguard/services/backend/internal/store"
	"github.com/phuoctmse/runguard/shared/types"
)

func TestApproveIncident(t *testing.T) {
	store := store.NewMemoryStore()
	id, _ := store.CreateIncident(nil, types.Incident{
		AlertName: "PodCrashLooping",
		Phase:     types.PhaseRequiresApproval,
	})

	h := NewWithStore(store)
	req := httptest.NewRequest(http.MethodPost, "/api/incidents/"+id+"/approve", nil)
	w := httptest.NewRecorder()

	h.ApproveIncident(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}

	inc, _ := store.GetIncident(nil, id)
	if inc.Phase != types.PhaseExecuting {
		t.Errorf("Phase = %q, want %q", inc.Phase, types.PhaseExecuting)
	}
}

func TestRejectIncident(t *testing.T) {
	store := store.NewMemoryStore()
	id, _ := store.CreateIncident(nil, types.Incident{
		AlertName: "PodCrashLooping",
		Phase:     types.PhaseRequiresApproval,
	})

	h := NewWithStore(store)
	req := httptest.NewRequest(http.MethodPost, "/api/incidents/"+id+"/reject", nil)
	w := httptest.NewRecorder()

	h.RejectIncident(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}

	inc, _ := store.GetIncident(nil, id)
	if inc.Phase != types.PhaseRejected {
		t.Errorf("Phase = %q, want %q", inc.Phase, types.PhaseRejected)
	}
}

func TestApproveIncidentWrongPhase(t *testing.T) {
	store := store.NewMemoryStore()
	id, _ := store.CreateIncident(nil, types.Incident{
		Phase: types.PhasePending,
	})

	h := NewWithStore(store)
	req := httptest.NewRequest(http.MethodPost, "/api/incidents/"+id+"/approve", nil)
	w := httptest.NewRecorder()

	h.ApproveIncident(w, req)

	if w.Code != http.StatusConflict {
		t.Errorf("status = %d, want %d", w.Code, http.StatusConflict)
	}
}
