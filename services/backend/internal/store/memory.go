package store

import (
	"context"
	"fmt"
	"sync"

	"github.com/phuoctmse/runguard/shared/types"
)

// MemoryStore is an in-memory implementation for incidents.
type MemoryStore struct {
	mu        sync.RWMutex
	incidents map[string]types.Incident
	nextID    int
}

// NewMemoryStore creates a new MemoryStore.
func NewMemoryStore() *MemoryStore {
	return &MemoryStore{
		incidents: make(map[string]types.Incident),
	}
}

// CreateIncident stores an incident and returns its ID.
func (s *MemoryStore) CreateIncident(ctx context.Context, inc types.Incident) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.nextID++
	id := fmt.Sprintf("inc-%d", s.nextID)
	s.incidents[id] = inc
	return id, nil
}

// GetIncident retrieves an incident by ID.
func (s *MemoryStore) GetIncident(ctx context.Context, id string) (*types.Incident, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	inc, ok := s.incidents[id]
	if !ok {
		return nil, fmt.Errorf("incident %q not found", id)
	}
	return &inc, nil
}

// ListIncidents returns all incidents.
func (s *MemoryStore) ListIncidents(ctx context.Context) ([]types.Incident, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]types.Incident, 0, len(s.incidents))
	for _, inc := range s.incidents {
		result = append(result, inc)
	}
	return result, nil
}
