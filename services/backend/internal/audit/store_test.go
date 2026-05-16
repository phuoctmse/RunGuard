package audit

import (
	"testing"
	"time"
)

func TestAuditStoreRecordIncident(t *testing.T) {
	store := NewMemoryAuditStore()

	record := Record{
		IncidentID: "inc-1",
		Type:       RecordTypeIncidentCreated,
		Timestamp:  time.Now(),
		Details: map[string]string{
			"alert_source": "alertmanager",
			"namespace":    "production",
			"workload":     "api-server",
		},
	}

	err := store.Append(record)
	if err != nil {
		t.Fatalf("Append failed: %v", err)
	}

	records, err := store.GetByIncident("inc-1")
	if err != nil {
		t.Fatalf("GetByIncident failed: %v", err)
	}
	if len(records) != 1 {
		t.Errorf("count = %d, want 1", len(records))
	}
}

func TestAuditStoreImmutable(t *testing.T) {
	store := NewMemoryAuditStore()

	store.Append(Record{IncidentID: "inc-1", Type: RecordTypeIncidentCreated, Timestamp: time.Now()})

	// Attempt to delete → should fail
	err := store.Delete("inc-1")
	if err == nil {
		t.Error("expected error for delete (immutable)")
	}

	// Attempt to update → should fail
	err = store.Update(Record{IncidentID: "inc-1", Type: RecordTypeActionExecuted})
	if err == nil {
		t.Error("expected error for update (immutable)")
	}
}

func TestAuditStoreChronological(t *testing.T) {
	store := NewMemoryAuditStore()

	t1 := time.Now()
	t2 := t1.Add(1 * time.Minute)
	t3 := t1.Add(2 * time.Minute)

	store.Append(Record{IncidentID: "inc-1", Type: RecordTypeActionExecuted, Timestamp: t3})
	store.Append(Record{IncidentID: "inc-1", Type: RecordTypeIncidentCreated, Timestamp: t1})
	store.Append(Record{IncidentID: "inc-1", Type: RecordTypePlanProduced, Timestamp: t2})

	records, _ := store.GetByIncident("inc-1")
	if records[0].Timestamp.After(records[1].Timestamp) {
		t.Error("records not in chronological order")
	}
}

func TestAuditStoreRollbackPath(t *testing.T) {
	store := NewMemoryAuditStore()

	store.Append(Record{
		IncidentID: "inc-1",
		Type:       RecordTypeActionExecuted,
		Timestamp:  time.Now(),
		Details: map[string]string{
			"action":       "restart",
			"rollback_cmd": "kubectl rollout undo deployment/api-server -n production",
		},
	})

	records, _ := store.GetByIncident("inc-1")
	if records[0].Details["rollback_cmd"] == "" {
		t.Error("rollback_cmd not stored")
	}
}

func TestAuditStoreGetByType(t *testing.T) {
	store := NewMemoryAuditStore()

	store.Append(Record{IncidentID: "inc-1", Type: RecordTypeIncidentCreated, Timestamp: time.Now()})
	store.Append(Record{IncidentID: "inc-1", Type: RecordTypeActionExecuted, Timestamp: time.Now()})
	store.Append(Record{IncidentID: "inc-1", Type: RecordTypeActionExecuted, Timestamp: time.Now()})

	records, _ := store.GetByType("inc-1", RecordTypeActionExecuted)
	if len(records) != 2 {
		t.Errorf("count = %d, want 2", len(records))
	}
}
