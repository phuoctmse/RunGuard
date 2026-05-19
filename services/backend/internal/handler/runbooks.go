package handler

import (
	"encoding/json"
	"net/http"

	apperrors "github.com/phuoctmse/runguard/shared/errors"
	"github.com/phuoctmse/runguard/shared/types"
)

// CreateRunbook handles POST /api/runbooks.
func (h *Handler) CreateRunbook(w http.ResponseWriter, r *http.Request) {
	var rb types.Runbook
	if err := json.NewDecoder(r.Body).Decode(&rb); err != nil {
		apperrors.WriteValidationError(w, "invalid JSON")
		return
	}

	id, err := h.runbookStore.CreateRunbook(r.Context(), rb)
	if err != nil {
		apperrors.WriteInternalError(w)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(map[string]string{"id": id})
}

// ListRunbooks handles GET /api/runbooks.
func (h *Handler) ListRunbooks(w http.ResponseWriter, r *http.Request) {
	runbooks, err := h.runbookStore.ListRunbooks(r.Context())
	if err != nil {
		apperrors.WriteInternalError(w)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(runbooks)
}
