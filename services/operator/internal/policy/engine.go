package policy

import (
	"github.com/phuoctmse/runguard/shared/types"
)

// Classification represents the result of policy validation.
type Classification string

const (
	Approved         Classification = "Approved"
	RequiresApproval Classification = "RequiresApproval"
	Blocked          Classification = "Blocked"
)

// ValidationResult holds the validation result for a single action.
type ValidationResult struct {
	Action         string         `json:"action"`
	Classification Classification `json:"classification"`
	Reason         string         `json:"reason"`
}

// Engine is the unified policy validation engine.
type Engine struct{}

func New() *Engine {
	return &Engine{}
}

// ValidatePlan validates all actions in a remediation plan against the policy.
func (e *Engine) ValidatePlan(
	actions []types.RemediationStep,
	policy types.Policy,
	runbook types.Runbook,
	environment string,
) []ValidationResult {
	results := make([]ValidationResult, 0, len(actions))

	for _, action := range actions {
		result := e.validateSingleAction(action, policy, runbook, environment)
		results = append(results, result)
	}

	return results
}

func (e *Engine) validateSingleAction(
	action types.RemediationStep,
	policy types.Policy,
	runbook types.Runbook,
	environment string,
) ValidationResult {
	proposed := types.ProposedAction{
		Action: action.Action,
		Target: action.Target,
		Risk:   action.Risk,
	}

	// 1. Check forbidden list (highest priority)
	if result := CheckForbidden(proposed, policy); result == Blocked {
		return ValidationResult{
			Action:         action.Name,
			Classification: Blocked,
			Reason:         "action is in forbidden list",
		}
	}

	// 2. Check blast radius (delete action)
	if result := CheckBlastRadiusAction(proposed, policy); result == Blocked {
		return ValidationResult{
			Action:         action.Name,
			Classification: Blocked,
			Reason:         "delete action forbidden by blast radius policy",
		}
	}

	// 3. Check scope
	if result := CheckScope(proposed, environment, policy); result == Blocked {
		return ValidationResult{
			Action:         action.Name,
			Classification: Blocked,
			Reason:         "action outside allowed scope",
		}
	}

	// 4. Check rollback path
	if result := CheckRollback(action, runbook); result == Blocked {
		return ValidationResult{
			Action:         action.Name,
			Classification: Blocked,
			Reason:         "missing rollback path",
		}
	}

	// 5. Check environment rules
	if result := CheckEnvironment(proposed, environment, policy); result == RequiresApproval {
		return ValidationResult{
			Action:         action.Name,
			Classification: RequiresApproval,
			Reason:         "production environment requires approval",
		}
	}

	return ValidationResult{
		Action:         action.Name,
		Classification: Approved,
		Reason:         "all checks passed",
	}
}

// ValidatePlanSafe wraps ValidatePlan with fail-safe: on error, all actions are blocked.
func (e *Engine) ValidatePlanSafe(
	actions []types.RemediationStep,
	policy types.Policy,
	runbook types.Runbook,
	environment string,
) (results []ValidationResult) {
	defer func() {
		if r := recover(); r != nil {
			results = make([]ValidationResult, len(actions))
			for i, action := range actions {
				results[i] = ValidationResult{
					Action:         action.Name,
					Classification: Blocked,
					Reason:         "panic during validation (fail-safe)",
				}
			}
		}
	}()

	if actions == nil {
		return []ValidationResult{{
			Action:         "unknown",
			Classification: Blocked,
			Reason:         "nil actions (fail-safe)",
		}}
	}

	return e.ValidatePlan(actions, policy, runbook, environment)
}

// ValidatePlanWithLimit enforces max auto-approved actions per incident [Req 11.5].
func (e *Engine) ValidatePlanWithLimit(
	actions []types.RemediationStep,
	policy types.Policy,
	runbook types.Runbook,
	environment string,
	maxAutoApproved int,
) []ValidationResult {
	results := e.ValidatePlan(actions, policy, runbook, environment)
	autoApprovedCount := 0

	for i := range results {
		if results[i].Classification == Approved {
			autoApprovedCount++
			if autoApprovedCount > maxAutoApproved {
				results[i].Classification = RequiresApproval
				results[i].Reason = "max auto-approved actions exceeded"
			}
		}
	}

	return results
}
