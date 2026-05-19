package store

// Store combines all store types.
type Store struct {
	*MemoryStore
	*RunbookStore
}

// NewStore creates a new Store with all sub-stores.
func NewStore() *Store {
	return &Store{
		MemoryStore:  NewMemoryStore(),
		RunbookStore: NewRunbookStore(),
	}
}

// HealthCheck returns nil for in-memory store (always available).
func (s *Store) HealthCheck() error {
	return nil
}
