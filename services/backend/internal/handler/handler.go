package handler

import (
	"encoding/json"
	"net/http"

	"backend/internal/store"
)

// Handler handles HTTP requests for the backend API.
type Handler struct {
	store *store.MemoryStore
}

// New creates a new Handler with a default store.
func New() *Handler {
	return &Handler{store: store.NewMemoryStore()}
}

// NewWithStore creates a new Handler with the given store.
func NewWithStore(s *store.MemoryStore) *Handler {
	return &Handler{store: s}
}

// Healthz returns 200 OK.
func (h *Handler) Healthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
