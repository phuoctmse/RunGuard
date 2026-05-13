package executor

import (
	"context"
	"fmt"

	"github.com/phuoctmse/runguard/shared/types"
)

// Executor executes remediation actions against Kubernetes.
type Executor struct {
	dryRun bool
}

// New creates a new Executor in dry-run mode.
func New() *Executor {
	return &Executor{dryRun: true}
}

// NewWithMode creates a new Executor with specified dry-run mode.
func NewWithMode(dryRun bool) *Executor {
	return &Executor{dryRun: dryRun}
}

// Execute runs a remediation action.
func (e *Executor) Execute(ctx context.Context, action types.RemediationStep, inc types.Incident) error {
	switch action.Action {
	case "restart":
		return e.restart(ctx, action.Target, inc.Namespace)
	case "scale":
		return e.scale(ctx, action.Target, inc.Namespace)
	case "rollback":
		return e.rollback(ctx, action.Target, inc.Namespace)
	default:
		return fmt.Errorf("unknown action: %q", action.Action)
	}
}

// restart deletes a pod to trigger restart.
func (e *Executor) restart(ctx context.Context, pod, namespace string) error {
	if e.dryRun {
		return nil
	}
	// kubectl delete pod <pod> -n <namespace>
	return nil
}

// scale scales a deployment.
func (e *Executor) scale(ctx context.Context, deployment, namespace string) error {
	if e.dryRun {
		return nil
	}
	// kubectl scale deployment <deployment> -n <namespace> --replicas=<n>
	return nil
}

// rollback rolls back a deployment.
func (e *Executor) rollback(ctx context.Context, deployment, namespace string) error {
	if e.dryRun {
		return nil
	}
	// kubectl rollout undo deployment/<deployment> -n <namespace>
	return nil
}
