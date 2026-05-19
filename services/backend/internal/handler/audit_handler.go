package handler

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
	apperrors "github.com/phuoctmse/runguard/shared/errors"
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
		apperrors.WriteError(w, http.StatusBadRequest, "missing incident id", "MISSING_ID")
		return
	}
	incidentID := parts[3]

	records, err := h.store.GetByIncident(incidentID)
	if err != nil {
		apperrors.WriteInternalError(w)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(records)
}
