package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/phuoctmse/runguard/services/backend/internal/store"
	"github.com/phuoctmse/runguard/shared/types"
)

type ApprovalHandler struct {
	store          *store.MemoryStore
	defaultTimeout time.Duration
	cancelFuncs    map[string]context.CancelFunc
	mu             sync.Mutex
}

func NewApprovalHandler(s *store.MemoryStore) *ApprovalHandler {
	return &ApprovalHandler{
		store:          s,
		defaultTimeout: 30 * time.Minute,
		cancelFuncs:    make(map[string]context.CancelFunc),
	}
}

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
	if err := h.store.UpdateIncident(r.Context(), id, *inc); err != nil {
		http.Error(w, `{"error":"failed to update incident"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "approved"})
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
	if err := h.store.UpdateIncident(r.Context(), id, *inc); err != nil {
		http.Error(w, `{"error":"failed to update incident"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "rejected"})
}

// extractID extracts the ID from a URL path.
func extractID(path, prefix, suffix string) string {
	if !strings.HasPrefix(path, prefix) {
		return ""
	}
	remaining := strings.TrimPrefix(path, prefix)
	return strings.TrimSuffix(remaining, suffix)
}

// StartApprovalTimeout starts a goroutine that auto-expires the approval after timeout.
func (h *ApprovalHandler) StartApprovalTimeout(incidentID string, timeout time.Duration) {
	h.mu.Lock()
	defer h.mu.Unlock()

	// Cancel any existing timeout for this incident
	if cancel, exists := h.cancelFuncs[incidentID]; exists {
		cancel()
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	h.cancelFuncs[incidentID] = cancel

	go func() {
		<-ctx.Done()

		// Check if context was cancelled (not timed out)
		if ctx.Err() != context.DeadlineExceeded {
			return
		}

		// Auto-expire the approval
		inc, err := h.store.GetIncident(context.Background(), incidentID)
		if err != nil {
			return
		}

		// Only expire if still in RequiresApproval
		if inc.Phase == types.PhaseRequiresApproval {
			inc.Phase = types.PhaseRejected
			h.store.UpdateIncident(context.Background(), incidentID, *inc)
		}

		h.mu.Lock()
		delete(h.cancelFuncs, incidentID)
		h.mu.Unlock()
	}()
}

// CancelTimeout cancels the approval timeout (called on approve/reject).
func (h *ApprovalHandler) CancelTimeout(incidentID string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if cancel, exists := h.cancelFuncs[incidentID]; exists {
		cancel()
		delete(h.cancelFuncs, incidentID)
	}
}

// Approve approves an incident and cancels the timeout.
func (h *ApprovalHandler) Approve(ctx context.Context, incidentID, approver string) error {
	h.CancelTimeout(incidentID)

	inc, err := h.store.GetIncident(ctx, incidentID)
	if err != nil {
		return err
	}

	inc.Phase = types.PhaseExecuting
	return h.store.UpdateIncident(ctx, incidentID, *inc)
}

// Reject rejects an incident and cancels the timeout.
func (h *ApprovalHandler) Reject(ctx context.Context, incidentID, rejector, reason string) error {
	h.CancelTimeout(incidentID)

	inc, err := h.store.GetIncident(ctx, incidentID)
	if err != nil {
		return err
	}

	inc.Phase = types.PhaseRejected
	return h.store.UpdateIncident(ctx, incidentID, *inc)
}
