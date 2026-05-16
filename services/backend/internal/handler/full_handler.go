package handler

import (
	"context"
	"time"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
	"github.com/phuoctmse/runguard/services/backend/internal/notify"
	"github.com/phuoctmse/runguard/services/backend/internal/store"
)

type FullHandler struct {
	store      *store.MemoryStore
	auditStore *audit.MemoryAuditStore
	notifier   notify.Notifier
	approval   *ApprovalHandler
}

func NewFullHandler(
	store *store.MemoryStore,
	auditStore *audit.MemoryAuditStore,
	slackWebhookURL string,
) *FullHandler {
	return &FullHandler{
		store:      store,
		auditStore: auditStore,
		notifier:   notify.NewSlackNotifier(slackWebhookURL),
		approval:   NewApprovalHandler(store),
	}
}

func (h *FullHandler) Approve(ctx context.Context, incidentID, approver string) error {
	// Update incident phase
	err := h.approval.Approve(ctx, incidentID, approver)
	if err != nil {
		return err
	}

	// Write audit record
	_ = h.auditStore.Append(audit.Record{
		IncidentID: incidentID,
		Type:       audit.RecordTypeActionApproved,
		Actor:      approver,
		Timestamp:  time.Now(),
	})

	// Send notification
	_ = h.notifier.NotifyApproved(incidentID, approver)

	return nil
}

func (h *FullHandler) Reject(ctx context.Context, incidentID, rejector, reason string) error {
	err := h.approval.Reject(ctx, incidentID, rejector, reason)
	if err != nil {
		return err
	}

	_ = h.auditStore.Append(audit.Record{
		IncidentID: incidentID,
		Type:       audit.RecordTypeActionRejected,
		Actor:      rejector,
		Timestamp:  time.Now(),
		Details:    map[string]string{"reason": reason},
	})

	_ = h.notifier.NotifyRejected(incidentID, rejector, reason)

	return nil
}
