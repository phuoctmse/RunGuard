package handler

import (
	"encoding/json"
	"net/http"

	"github.com/phuoctmse/runguard/services/backend/internal/store"
)

// Handler handles HTTP requests for the backend API.
type Handler struct {
	store        *store.MemoryStore
	runbookStore *store.RunbookStore
}

// New creates a new Handler with default stores.
func New() *Handler {
	return &Handler{
		store:        store.NewMemoryStore(),
		runbookStore: store.NewRunbookStore(),
	}
}

// NewWithStore creates a new Handler with the given store.
func NewWithStore(s *store.MemoryStore) *Handler {
	return &Handler{
		store:        s,
		runbookStore: store.NewRunbookStore(),
	}
}

// Healthz returns 200 OK.
func (h *Handler) Healthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
