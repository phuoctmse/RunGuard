package compiler

import (
	"testing"
)

func TestRunbookVersioning(t *testing.T) {
	store := NewVersionedStore()

	md1 := []byte(`# Runbook V1
## Scope
- Namespaces: production
## Remediation
### Restart
- Action: restart
- Risk: low
## Rollback
### Undo
- Action: rollback
- Risk: low
`)
	v1, err := store.Store("PodCrashLooping", md1)
	if err != nil {
		t.Fatalf("store v1 failed: %v", err)
	}
	if v1 != 1 {
		t.Errorf("version = %d, want 1", v1)
	}

	md2 := []byte(`# Runbook V2
## Scope
- Namespaces: production, staging
## Remediation
### Restart
- Action: restart
- Risk: low
## Rollback
### Undo
- Action: rollback
- Risk: low
`)
	v2, _ := store.Store("PodCrashLooping", md2)
	if v2 != 2 {
		t.Errorf("version = %d, want 2", v2)
	}

	// V1 should still exist
	_, err = store.Get("PodCrashLooping", 1)
	if err != nil {
		t.Errorf("v1 should still exist: %v", err)
	}
}

func TestRunbookVersioningLatest(t *testing.T) {
	store := NewVersionedStore()

	md := []byte(`# Runbook
## Scope
- Namespaces: production
## Remediation
### Restart
- Action: restart
- Risk: low
## Rollback
### Undo
- Action: rollback
- Risk: low
`)

	store.Store("test-runbook", md)
	store.Store("test-runbook", md)

	latest, err := store.GetLatest("test-runbook")
	if err != nil {
		t.Fatalf("GetLatest failed: %v", err)
	}
	if latest.Version != 2 {
		t.Errorf("latest version = %d, want 2", latest.Version)
	}
}
