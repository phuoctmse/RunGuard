package handler

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/phuoctmse/runguard/shared/types"
)

// CreateIncident handles POST /api/incidents.
func (h *Handler) CreateIncident(w http.ResponseWriter, r *http.Request) {
	var inc types.Incident
	if err := json.NewDecoder(r.Body).Decode(&inc); err != nil {
		http.Error(w, `{"error":"invalid JSON"}`, http.StatusBadRequest)
		return
	}

	inc.Phase = types.PhasePending
	id, err := h.store.CreateIncident(r.Context(), inc)
	if err != nil {
		http.Error(w, `{"error":"failed to create"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(map[string]string{"id": id})
}

// ListIncidents handles GET /api/incidents.
func (h *Handler) ListIncidents(w http.ResponseWriter, r *http.Request) {
	incidents, err := h.store.ListIncidents(r.Context())
	if err != nil {
		http.Error(w, `{"error":"failed to list"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(incidents)
}

// GetIncident handles GET /api/incidents/{id}.
func (h *Handler) GetIncident(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/api/incidents/")
	if id == "" {
		http.Error(w, `{"error":"missing id"}`, http.StatusBadRequest)
		return
	}

	inc, err := h.store.GetIncident(r.Context(), id)
	if err != nil {
		http.Error(w, `{"error":"not found"}`, http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(inc)
}
