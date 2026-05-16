package handler

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
)

type AuditHandler struct {
	store *audit.MemoryAuditStore
}

func NewWithAuditStore(store *audit.MemoryAuditStore) *AuditHandler {
	return &AuditHandler{store: store}
}

// GetAuditTrail handles GET /api/audit/{id}
func (h *AuditHandler) GetAuditTrail(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 || parts[3] == "" {
		http.Error(w, `{"error":"missing incident id"}`, http.StatusBadRequest)
		return
	}
	incidentID := parts[3]

	records, err := h.store.GetByIncident(incidentID)
	if err != nil {
		http.Error(w, `{"error":"`+err.Error()+`"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(records)
}
