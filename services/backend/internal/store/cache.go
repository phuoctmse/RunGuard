package store

import "sync"

// Cache defines the caching interface.
type Cache interface {
	Get(key string) ([]byte, bool)
	Set(key string, value []byte)
	Delete(key string)
}

// MemoryCache is an in-memory cache implementation.
type MemoryCache struct {
	mu    sync.RWMutex
	items map[string][]byte
}

// NewMemoryCache creates a new MemoryCache.
func NewMemoryCache() *MemoryCache {
	return &MemoryCache{items: make(map[string][]byte)}
}

// Get retrieves a value from the cache.
func (c *MemoryCache) Get(key string) ([]byte, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	val, ok := c.items[key]
	return val, ok
}

// Set stores a value in the cache.
func (c *MemoryCache) Set(key string, value []byte) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.items[key] = value
}

// Delete removes a value from the cache.
func (c *MemoryCache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.items, key)
}
