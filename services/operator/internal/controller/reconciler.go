package controller

import (
	"context"
	"fmt"
	"log"

	"github.com/phuoctmse/runguard/services/operator/internal/policy"
	"github.com/phuoctmse/runguard/shared/types"
)

var logger = log.Default()

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

type ReasonerClient interface {
	Analyze(ctx context.Context, alert, namespace string, evidence map[string]string) (*ReasonerResult, error)
}

type ReasonerResult struct {
	RootCause  string   `json:"root_cause"`
	Confidence float64  `json:"confidence"`
	Actions    []string `json:"actions"`
}

type ReconcilerWithReasoner struct {
	store    *MemoryIncidentStore
	runbooks []types.Runbook
	executor *MockExecutor
	reasoner ReasonerClient
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

func NewReconcilerWithReasoner(
	store *MemoryIncidentStore,
	runbooks []types.Runbook,
	exec *MockExecutor,
	reasoner ReasonerClient,
) *ReconcilerWithReasoner {
	return &ReconcilerWithReasoner{
		store:    store,
		runbooks: runbooks,
		executor: exec,
		reasoner: reasoner,
	}
}

func (r *ReconcilerWithReasoner) Reconcile(ctx context.Context, id string) error {
	inc, err := r.store.Get(ctx, id)
	if err != nil {
		return err
	}

	// Match runbook
	runbook := r.matchRunbook(inc.AlertName, inc.Severity)
	if runbook == nil {
		inc.Phase = types.PhaseFailed
		r.store.Update(ctx, id, *inc)
		return fmt.Errorf("no matching runbook")
	}

	// Transition to Analyzing
	inc.Phase = types.PhaseAnalyzing
	r.store.Update(ctx, id, *inc)

	// Collect evidence (placeholder)
	evidence := map[string]string{
		"namespace": inc.Namespace,
		"workload":  inc.Workload,
	}

	// Call reasoner (with fallback on timeout)
	_, reasonerErr := r.reasoner.Analyze(
		ctx, inc.AlertName, inc.Namespace, evidence,
	)

	if reasonerErr != nil {
		logger.Printf("Reasoner failed: %v, proceeding with rule-based", reasonerErr)
	}

	// Execute remediation
	inc.Phase = types.PhaseExecuting
	r.store.Update(ctx, id, *inc)

	for _, step := range runbook.Remediation {
		if err := r.executor.Execute(ctx, step, *inc); err != nil {
			inc.Phase = types.PhaseFailed
			r.store.Update(ctx, id, *inc)
			return err
		}
	}

	inc.Phase = types.PhaseResolved
	r.store.Update(ctx, id, *inc)
	return nil
}

func (r *ReconcilerWithReasoner) matchRunbook(alertName, severity string) *types.Runbook {
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
