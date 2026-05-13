package controller

import (
	"context"
	"fmt"

	"github.com/phuoctmse/runguard/shared/types"
)

// Executor executes remediation actions.
type Executor interface {
	Execute(ctx context.Context, action types.RemediationStep, inc types.Incident) error
}

// Reconciler processes incidents through the lifecycle.
type Reconciler struct {
	store    *MemoryIncidentStore
	runbooks []types.Runbook
	executor Executor
}

// NewReconciler creates a new Reconciler.
func NewReconciler(store *MemoryIncidentStore, runbooks []types.Runbook, executor Executor) *Reconciler {
	return &Reconciler{
		store:    store,
		runbooks: runbooks,
		executor: executor,
	}
}

// Reconcile processes a single incident through the lifecycle.
func (r *Reconciler) Reconcile(ctx context.Context, id string) error {
	inc, err := r.store.Get(ctx, id)
	if err != nil {
		return err
	}

	// Step 1: Match runbook
	rb, matched := MatchRunbook(*inc, r.runbooks)
	if !matched {
		inc.Phase = types.PhaseFailed
		r.store.Update(ctx, id, *inc)
		return fmt.Errorf("no matching runbook for alert %q", inc.AlertName)
	}

	// Step 2: Analyze
	inc.Phase = types.PhaseAnalyzing
	r.store.Update(ctx, id, *inc)

	// Step 3: Execute auto-approved remediation
	for _, step := range rb.Remediation {
		if step.AutoApprove && step.Risk == "low" {
			if r.executor != nil {
				if err := r.executor.Execute(ctx, step, *inc); err != nil {
					inc.Phase = types.PhaseFailed
					r.store.Update(ctx, id, *inc)
					return fmt.Errorf("execute %q failed: %w", step.Name, err)
				}
			}
		} else {
			// Needs approval
			inc.Phase = types.PhaseRequiresApproval
			r.store.Update(ctx, id, *inc)
			return nil
		}
	}

	// Step 4: Resolved
	inc.Phase = types.PhaseResolved
	r.store.Update(ctx, id, *inc)
	return nil
}
