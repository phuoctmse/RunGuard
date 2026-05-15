package compiler

import (
	"encoding/json"
	"testing"
)

func TestGeneratePolicy(t *testing.T) {
	runbook := ParsedRunbook{
		Title:     "PodCrashLooping",
		Scope:     RunbookScope{Namespaces: []string{"production"}, Resources: []string{"deployments", "pods"}},
		Forbidden: []string{"delete_namespace"},
		Remediation: []ParsedStep{
			{Action: "restart", Risk: "low", AutoApprove: true},
		},
		Rollback: []ParsedStep{
			{Action: "rollback", Risk: "low"},
		},
	}

	policy := GeneratePolicy(&runbook)

	if len(policy.Scope.Namespace) != 1 {
		t.Errorf("Namespaces count = %d, want 1", len(policy.Scope.Namespace))
	}
	if policy.BlastRadius.ForbidDelete {
		t.Error("ForbidDelete should be false for this runbook")
	}
	if len(policy.Forbidden) != 1 {
		t.Errorf("Forbidden count = %d, want 1", len(policy.Forbidden))
	}
}

func TestRoundTrip(t *testing.T) {
	md := `# Test Runbook

## Scope
- Namespaces: production
- Resources: pods

## Severity
critical

## Remediation
### Restart
- Action: restart
- Target: pod
- Risk: low
- AutoApprove: true

## Rollback
### Undo
- Action: rollback
- Target: pod
- Risk: low
`

	runbook1, err := ParseMarkdown([]byte(md))
	if err != nil {
		t.Fatalf("first parse failed: %v", err)
	}
	policy1 := GeneratePolicy(runbook1)

	runbook2, _ := ParseMarkdown([]byte(md))
	policy2 := GeneratePolicy(runbook2)

	p1, _ := json.Marshal(policy1)
	p2, _ := json.Marshal(policy2)

	if string(p1) != string(p2) {
		t.Errorf("round-trip produced different policies:\n%s\n%s", p1, p2)
	}
}
