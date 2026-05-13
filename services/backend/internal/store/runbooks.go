package store

import (
	"context"
	"fmt"
	"sync"

	"github.com/phuoctmse/runguard/shared/types"
)

// RunbookStore stores runbooks in memory.
type RunbookStore struct {
	mu       sync.RWMutex
	runbooks map[string]types.Runbook
	nextID   int
}

// NewRunbookStore creates a new RunbookStore.
func NewRunbookStore() *RunbookStore {
	return &RunbookStore{
		runbooks: make(map[string]types.Runbook),
	}
}

// CreateRunbook stores a runbook and returns its ID.
func (s *RunbookStore) CreateRunbook(ctx context.Context, rb types.Runbook) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.nextID++
	id := fmt.Sprintf("rb-%d", s.nextID)
	s.runbooks[id] = rb
	return id, nil
}

// ListRunbooks returns all runbooks.
func (s *RunbookStore) ListRunbooks(ctx context.Context) ([]types.Runbook, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]types.Runbook, 0, len(s.runbooks))
	for _, rb := range s.runbooks {
		result = append(result, rb)
	}
	return result, nil
}
