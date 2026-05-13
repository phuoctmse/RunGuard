package controller

import (
	"context"
	"fmt"
	"sync"

	"github.com/phuoctmse/runguard/shared/types"
)

// MemoryIncidentStore stores incidents in memory.
type MemoryIncidentStore struct {
	mu        sync.RWMutex
	incidents map[string]types.Incident
	nextID    int
}

// NewMemoryIncidentStore creates a new in-memory incident store.
func NewMemoryIncidentStore() *MemoryIncidentStore {
	return &MemoryIncidentStore{
		incidents: make(map[string]types.Incident),
	}
}

// Create stores an incident and returns its ID.
func (s *MemoryIncidentStore) Create(ctx context.Context, inc types.Incident) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.nextID++
	id := fmt.Sprintf("inc-%d", s.nextID)
	s.incidents[id] = inc
	return id, nil
}

// Get retrieves an incident by ID.
func (s *MemoryIncidentStore) Get(ctx context.Context, id string) (*types.Incident, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	inc, ok := s.incidents[id]
	if !ok {
		return nil, fmt.Errorf("incident %q not found", id)
	}
	return &inc, nil
}

// Update updates an existing incident.
func (s *MemoryIncidentStore) Update(ctx context.Context, id string, inc types.Incident) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.incidents[id]; !ok {
		return fmt.Errorf("incident %q not found", id)
	}
	s.incidents[id] = inc
	return nil
}

// List returns all incidents.
func (s *MemoryIncidentStore) List(ctx context.Context) ([]types.Incident, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]types.Incident, 0, len(s.incidents))
	for _, inc := range s.incidents {
		result = append(result, inc)
	}
	return result, nil
}
