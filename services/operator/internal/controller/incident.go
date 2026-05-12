package controller

import "github.com/phuoctmse/runguard/shared/types"

func MatchRunbook(inc types.Incident, runbooks []types.Runbook) (*types.Runbook, bool) {
	for _, rb := range runbooks {
		if rb.AlertName != inc.AlertName {
			continue
		}
		for _, sev := range rb.Severity {
			if sev == inc.Severity {
				return &rb, true
			}
		}
	}
	return nil, false
}

// ClassifyRisk returns the risk level for a given action type.
func ClassifyRisk(action string) string {
	switch action {
	case "restart":
		return "low"
	case "scale", "patch":
		return "medium"
	case "rollback", "delete":
		return "high"
	default:
		return "medium"
	}
}
