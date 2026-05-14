package compiler

import (
	"fmt"
	"sync"
)

// VersionedEntry holds a specific version of a runbook.
type VersionedEntry struct {
	Version int
	Name    string
	Raw     []byte
	Runbook *ParsedRunbook
}

// VersionedStore is an append-only store for runbook versions.
type VersionedStore struct {
	mu      sync.RWMutex
	entries map[string][]VersionedEntry // key: runbook name
}

func NewVersionedStore() *VersionedStore {
	return &VersionedStore{
		entries: make(map[string][]VersionedEntry),
	}
}

// Store saves a new version of a runbook. Returns the version number.
func (s *VersionedStore) Store(name string, data []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	runbook, err := ParseMarkdown(data)
	if err != nil {
		return 0, fmt.Errorf("parse failed: %w", err)
	}

	versions := s.entries[name]
	newVersion := len(versions) + 1

	s.entries[name] = append(versions, VersionedEntry{
		Version: newVersion,
		Name:    name,
		Raw:     data,
		Runbook: runbook,
	})

	return newVersion, nil
}

// Get retrieves a specific version of a runbook.
func (s *VersionedStore) Get(name string, version int) (*VersionedEntry, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	versions, ok := s.entries[name]
	if !ok {
		return nil, fmt.Errorf("runbook %q not found", name)
	}

	for _, v := range versions {
		if v.Version == version {
			return &v, nil
		}
	}

	return nil, fmt.Errorf("version %d not found for runbook %q", version, name)
}

// GetLatest retrieves the latest version of a runbook.
func (s *VersionedStore) GetLatest(name string) (*VersionedEntry, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	versions, ok := s.entries[name]
	if !ok || len(versions) == 0 {
		return nil, fmt.Errorf("runbook %q not found", name)
	}

	latest := versions[len(versions)-1]
	return &latest, nil
}

// ListVersions returns all version numbers for a runbook.
func (s *VersionedStore) ListVersions(name string) []int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	versions := s.entries[name]
	result := make([]int, len(versions))
	for i, v := range versions {
		result[i] = v.Version
	}
	return result
}
