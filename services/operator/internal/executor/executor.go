package executor

import (
	"context"
	"fmt"

	"github.com/phuoctmse/runguard/shared/types"
)

// Executor executes remediation actions against Kubernetes.
type Executor struct {
	dryRun      bool
	failAction  string
	RollbackLog []string
}

// New creates a new Executor in dry-run mode.
func New() *Executor {
	return &Executor{dryRun: true}
}

// NewWithMode creates a new Executor with specified dry-run mode.
func NewWithMode(dryRun bool) *Executor {
	return &Executor{
		dryRun:      dryRun,
		RollbackLog: make([]string, 0),
	}
}

func (e *Executor) SetFailAction(action string) {
	e.failAction = action
}

// ExecuteWithRollback executes actions sequentially. On failure, rolls back in reverse order [Req 11.4].
func (e *Executor) ExecuteWithRollback(
	ctx context.Context,
	actions []types.RemediationStep,
	rollbackSteps []types.RemediationStep,
	incident types.Incident,
) error {
	executedSteps := make([]types.RemediationStep, 0, len(actions))

	for _, step := range actions {
		executedSteps = append(executedSteps, step)
		if err := e.Execute(ctx, step, incident); err != nil {
			// Failure — roll back in reverse order (include the failed step)
			e.rollback(ctx, executedSteps, rollbackSteps, incident)
			return fmt.Errorf("action %q failed: %w", step.Name, err)
		}
	}

	return nil
}

func (e *Executor) executeRollback(ctx context.Context, step types.RemediationStep, incident types.Incident) {
	if e.dryRun {
		return
	}
	// Real implementation would call kubectl/API
}

// Execute runs a single remediation step.
func (e *Executor) Execute(ctx context.Context, step types.RemediationStep, incident types.Incident) error {
	if e.failAction != "" && step.Action == e.failAction {
		return fmt.Errorf("simulated failure for action %q", step.Action)
	}

	// Validate action before checking dryRun
	switch step.Action {
	case "restart", "scale", "rollback":
		// valid actions
	default:
		return fmt.Errorf("unknown action: %s", step.Action)
	}

	if e.dryRun {
		return nil
	}

	switch step.Action {
	case "restart":
		return e.executeRestart(ctx, step, incident)
	case "scale":
		return e.executeScale(ctx, step, incident)
	case "rollback":
		e.executeRollback(ctx, step, incident)
		return nil
	default:
		return fmt.Errorf("unknown action: %s", step.Action)
	}
}

func (e *Executor) executeRestart(ctx context.Context, step types.RemediationStep, incident types.Incident) error {
	// kubectl rollout restart deployment/{target} -n {namespace}
	return nil
}

func (e *Executor) executeScale(ctx context.Context, step types.RemediationStep, incident types.Incident) error {
	// kubectl scale deployment/{target} --replicas={n} -n {namespace}
	return nil
}

// // restart deletes a pod to trigger restart.
// func (e *Executor) restart(ctx context.Context, pod, namespace string) error {
// 	if e.dryRun {
// 		return nil
// 	}
// 	// kubectl delete pod <pod> -n <namespace>
// 	return nil
// }

// // scale scales a deployment.
// func (e *Executor) scale(ctx context.Context, deployment, namespace string) error {
// 	if e.dryRun {
// 		return nil
// 	}
// 	// kubectl scale deployment <deployment> -n <namespace> --replicas=<n>
// 	return nil
// }

// rollback executes rollback steps in reverse order.
func (e *Executor) rollback(
	ctx context.Context,
	executedSteps []types.RemediationStep,
	rollbackSteps []types.RemediationStep,
	incident types.Incident,
) {
	// Reverse the executed steps
	for i := len(executedSteps) - 1; i >= 0; i-- {
		step := executedSteps[i]

		// Find matching rollback step
		for _, rb := range rollbackSteps {
			if rb.Name == "undo_"+step.Name {
				e.RollbackLog = append(e.RollbackLog, rb.Name)
				// Execute rollback (ignore errors — best effort)
				e.executeRollback(ctx, rb, incident)
				break
			}
		}
	}
}
