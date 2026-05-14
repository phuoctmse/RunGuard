package compiler

import (
	"testing"
)

func TestParseValidRunbook(t *testing.T) {
	md := `# PodCrashLooping Runbook

## Scope
- Namespaces: production, staging
- Resources: deployments, pods

## Severity
critical, warning

## Allowed Tools
- kubectl logs
- kubectl describe
- kubectl rollout restart

## Forbidden Tools
- kubectl delete namespace
- kubectl edit rbac

## Diagnosis
### Check Logs
` + "```" + `
kubectl logs {{.PodName}} -n {{.Namespace}} --tail=100
` + "```" + `

### Check Events
` + "```" + `
kubectl get events -n {{.Namespace}} --field-selector involvedObject.name={{.PodName}}
` + "```" + `

## Remediation
### Restart Pod
- Action: restart
- Target: {{.PodName}}
- Risk: low
- AutoApprove: true

## Rollback
### Undo Restart
- Action: rollback
- Target: {{.PodName}}
- Risk: low
`

	runbook, err := ParseMarkdown([]byte(md))
	if err != nil {
		t.Fatalf("ParseMarkdown failed: %v", err)
	}

	if runbook.Title != "PodCrashLooping Runbook" {
		t.Errorf("Title = %q, want %q", runbook.Title, "PodCrashLooping Runbook")
	}
	if len(runbook.Scope.Namespaces) != 2 {
		t.Errorf("Namespaces count = %d, want 2", len(runbook.Scope.Namespaces))
	}
	if len(runbook.Diagnosis) != 2 {
		t.Errorf("Diagnosis count = %d, want 2", len(runbook.Diagnosis))
	}
	if len(runbook.Remediation) != 1 {
		t.Errorf("Remediation count = %d, want 1", len(runbook.Remediation))
	}
	if runbook.Remediation[0].Risk != "low" {
		t.Errorf("Risk = %q, want %q", runbook.Remediation[0].Risk, "low")
	}
}

func TestParseMissingRollback(t *testing.T) {
	md := `# Test Runbook

## Scope
- Namespaces: production

## Remediation
### Do Something
- Action: restart
- Target: pod
- Risk: low
`

	_, err := ParseMarkdown([]byte(md))
	if err == nil {
		t.Error("expected error for missing rollback section")
	}
}

func TestParseInvalidSyntax(t *testing.T) {
	md := []byte("not a valid runbook at all")

	_, err := ParseMarkdown(md)
	if err == nil {
		t.Error("expected error for invalid syntax")
	}
}
