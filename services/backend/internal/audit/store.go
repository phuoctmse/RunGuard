package audit

import (
	"fmt"
	"sort"
	"sync"
	"time"
)

// RecordType represents the type of audit event.
type RecordType string

const (
	RecordTypeIncidentCreated  RecordType = "incident_created"
	RecordTypePlanProduced     RecordType = "plan_produced"
	RecordTypeActionApproved   RecordType = "action_approved"
	RecordTypeActionRejected   RecordType = "action_rejected"
	RecordTypeActionExecuted   RecordType = "action_executed"
	RecordTypeActionFailed     RecordType = "action_failed"
	RecordTypeRollbackExecuted RecordType = "rollback_executed"
	RecordTypeApprovalTimeout  RecordType = "approval_timeout"
)

// Record is a single audit trail entry.
type Record struct {
	IncidentID string            `json:"incident_id"`
	Type       RecordType        `json:"type"`
	Timestamp  time.Time         `json:"timestamp"`
	Actor      string            `json:"actor,omitempty"` // who performed the action
	Details    map[string]string `json:"details,omitempty"`
}

// MemoryAuditStore is an append-only in-memory audit store.
type MemoryAuditStore struct {
	mu      sync.RWMutex
	records []Record
}

func NewMemoryAuditStore() *MemoryAuditStore {
	return &MemoryAuditStore{
		records: make([]Record, 0),
	}
}

// Append adds a record to the audit trail. Cannot be modified after.
func (s *MemoryAuditStore) Append(record Record) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if record.Timestamp.IsZero() {
		record.Timestamp = time.Now()
	}

	s.records = append(s.records, record)
	return nil
}

// GetByIncident returns all records for an incident in chronological order.
func (s *MemoryAuditStore) GetByIncident(incidentID string) ([]Record, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var result []Record
	for _, r := range s.records {
		if r.IncidentID == incidentID {
			result = append(result, r)
		}
	}

	sort.Slice(result, func(i, j int) bool {
		return result[i].Timestamp.Before(result[j].Timestamp)
	})

	return result, nil
}

// GetByType returns records of a specific type for an incident.
func (s *MemoryAuditStore) GetByType(incidentID string, recordType RecordType) ([]Record, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var result []Record
	for _, r := range s.records {
		if r.IncidentID == incidentID && r.Type == recordType {
			result = append(result, r)
		}
	}

	sort.Slice(result, func(i, j int) bool {
		return result[i].Timestamp.Before(result[j].Timestamp)
	})

	return result, nil
}

// Delete is not allowed — audit records are immutable [Req 7.6].
func (s *MemoryAuditStore) Delete(incidentID string) error {
	return fmt.Errorf("audit records are immutable (delete not allowed)")
}

// Update is not allowed — audit records are immutable [Req 7.6].
func (s *MemoryAuditStore) Update(record Record) error {
	return fmt.Errorf("audit records are immutable (update not allowed)")
}
