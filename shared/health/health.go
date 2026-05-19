package health

import (
	"encoding/json"
	"net/http"
	"sync"
)

type Checker struct {
	service string
	checks  map[string]func() error
	mu      sync.RWMutex
}

func New(service string) *Checker {
	return &Checker{
		service: service,
		checks:  make(map[string]func() error),
	}
}

func (c *Checker) AddCheck(name string, check func() error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.checks[name] = check
}

// LiveHandler returns 200 if process is alive.
func (c *Checker) LiveHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(map[string]string{"status": "alive"})
	}
}

// ReadyHandler returns 200 only if all checks pass.
func (c *Checker) ReadyHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		c.mu.RLock()
		defer c.mu.RUnlock()

		for name, check := range c.checks {
			if err := check(); err != nil {
				w.WriteHeader(http.StatusServiceUnavailable)
				_ = json.NewEncoder(w).Encode(map[string]string{
					"status": "not ready",
					"error":  name + ": " + err.Error(),
				})
				return
			}
		}

		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
	}
}
