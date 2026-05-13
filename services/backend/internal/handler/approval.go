package handler

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/phuoctmse/runguard/shared/types"
)

// ApproveIncident handles POST /api/incidents/{id}/approve.
func (h *Handler) ApproveIncident(w http.ResponseWriter, r *http.Request) {
	id := extractID(r.URL.Path, "/api/incidents/", "/approve")
	if id == "" {
		http.Error(w, `{"error":"missing id"}`, http.StatusBadRequest)
		return
	}

	inc, err := h.store.GetIncident(r.Context(), id)
	if err != nil {
		http.Error(w, `{"error":"not found"}`, http.StatusNotFound)
		return
	}

	if inc.Phase != types.PhaseRequiresApproval {
		http.Error(w, `{"error":"incident not in RequiresApproval phase"}`, http.StatusConflict)
		return
	}

	inc.Phase = types.PhaseExecuting
	h.store.UpdateIncident(r.Context(), id, *inc)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "approved"})
}

// RejectIncident handles POST /api/incidents/{id}/reject.
func (h *Handler) RejectIncident(w http.ResponseWriter, r *http.Request) {
	id := extractID(r.URL.Path, "/api/incidents/", "/reject")
	if id == "" {
		http.Error(w, `{"error":"missing id"}`, http.StatusBadRequest)
		return
	}

	inc, err := h.store.GetIncident(r.Context(), id)
	if err != nil {
		http.Error(w, `{"error":"not found"}`, http.StatusNotFound)
		return
	}

	if inc.Phase != types.PhaseRequiresApproval {
		http.Error(w, `{"error":"incident not in RequiresApproval phase"}`, http.StatusConflict)
		return
	}

	inc.Phase = types.PhaseRejected
	h.store.UpdateIncident(r.Context(), id, *inc)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "rejected"})
}

// extractID extracts the ID from a URL path.
func extractID(path, prefix, suffix string) string {
	if !strings.HasPrefix(path, prefix) {
		return ""
	}
	remaining := strings.TrimPrefix(path, prefix)
	return strings.TrimSuffix(remaining, suffix)
}
