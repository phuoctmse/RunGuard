package store

import (
	"testing"
)

func TestCacheInterface(t *testing.T) {
	// Verify MemoryCache implements Cache interface
	var _ Cache = (*MemoryCache)(nil)
}

func TestMemoryCacheGetSet(t *testing.T) {
	c := NewMemoryCache()

	// Get on empty cache
	_, ok := c.Get("key1")
	if ok {
		t.Error("expected cache miss")
	}

	// Set and Get
	c.Set("key1", []byte(`{"alertName":"test"}`))
	val, ok := c.Get("key1")
	if !ok {
		t.Error("expected cache hit")
	}
	if string(val) != `{"alertName":"test"}` {
		t.Errorf("val = %q", string(val))
	}
}

func TestMemoryCacheDelete(t *testing.T) {
	c := NewMemoryCache()
	c.Set("key1", []byte("value"))
	c.Delete("key1")

	_, ok := c.Get("key1")
	if ok {
		t.Error("expected cache miss after delete")
	}
}
