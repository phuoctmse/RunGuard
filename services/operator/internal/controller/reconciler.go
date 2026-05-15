package controller

import (
	"context"
	"fmt"

	"github.com/phuoctmse/runguard/services/operator/internal/policy"
	"github.com/phuoctmse/runguard/shared/types"
)

// Executor executes remediation actions.
type Executor interface {
	Execute(ctx context.Context, step types.RemediationStep, inc types.Incident) error
}

// ReconcilerWithPolicy extends Reconciler with policy validation.
type ReconcilerWithPolicy struct {
	store        *MemoryIncidentStore
	runbooks     []types.Runbook
	executor     Executor
	policy       types.Policy
	policyEngine *policy.Engine
}

func NewReconcilerWithPolicy(
	store *MemoryIncidentStore,
	runbooks []types.Runbook,
	exec Executor,
	pol types.Policy,
) *ReconcilerWithPolicy {
	return &ReconcilerWithPolicy{
		store:        store,
		runbooks:     runbooks,
		executor:     exec,
		policy:       pol,
		policyEngine: policy.New(),
	}
}

func (r *ReconcilerWithPolicy) Reconcile(ctx context.Context, id string) error {
	inc, err := r.store.Get(ctx, id)
	if err != nil {
		return err
	}

	// Match runbook
	runbook := r.matchRunbook(inc.AlertName, inc.Severity)
	if runbook == nil {
		inc.Phase = types.PhaseFailed
		_ = r.store.Update(ctx, id, *inc)
		return fmt.Errorf("no matching runbook")
	}

	// Validate with policy engine
	results := r.policyEngine.ValidatePlan(
		runbook.Remediation,
		r.policy,
		*runbook,
		inc.Namespace,
	)

	// Check for blocked actions
	for _, result := range results {
		if result.Classification == policy.Blocked {
			inc.Phase = types.PhaseFailed
			_ = r.store.Update(ctx, id, *inc)
			return fmt.Errorf("action %q blocked: %s", result.Action, result.Reason)
		}
	}

	// Check if any action requires approval
	for _, result := range results {
		if result.Classification == policy.RequiresApproval {
			inc.Phase = types.PhaseRequiresApproval
			_ = r.store.Update(ctx, id, *inc)
			return nil
		}
	}

	// All approved — execute
	inc.Phase = types.PhaseExecuting
	_ = r.store.Update(ctx, id, *inc)

	for _, step := range runbook.Remediation {
		if err := r.executor.Execute(ctx, step, *inc); err != nil {
			inc.Phase = types.PhaseFailed
			_ = r.store.Update(ctx, id, *inc)
			return err
		}
	}

	inc.Phase = types.PhaseResolved
	_ = r.store.Update(ctx, id, *inc)
	return nil
}
<<<<<<< HEAD

func (r *ReconcilerWithPolicy) matchRunbook(alertName, severity string) *types.Runbook {
	for _, rb := range r.runbooks {
		if rb.AlertName == alertName {
			for _, s := range rb.Severity {
				if s == severity {
					return &rb
				}
			}
		}
	}
	return nil
}
=======
>>>>>>> fae3ab7439e294f06ad6a86cb22c976cc56fde3b
