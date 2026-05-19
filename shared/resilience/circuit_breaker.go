package resilience

import (
	"errors"
	"sync"
	"time"
)

var ErrCircuitOpen = errors.New("circuit breaker is open")

type CircuitState int

const (
	StateClosed CircuitState = iota
	StateOpen
	StateHalfOpen
)

func (s CircuitState) String() string {
	switch s {
	case StateClosed:
		return "closed"
	case StateOpen:
		return "open"
	case StateHalfOpen:
		return "half-open"
	default:
		return "unknown"
	}
}

type CircuitBreaker struct {
	name          string
	maxFailures   uint32
	timeout       time.Duration
	failures      uint32
	state         CircuitState
	lastFailureAt time.Time
	mu            sync.Mutex
}

func NewCircuitBreaker(name string, maxFailures uint32, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		name:        name,
		maxFailures: maxFailures,
		timeout:     timeout,
		state:       StateClosed,
	}
}

func (cb *CircuitBreaker) Execute(fn func() (any, error)) (any, error) {
	cb.mu.Lock()

	if cb.state == StateOpen {
		if time.Since(cb.lastFailureAt) > cb.timeout {
			cb.state = StateHalfOpen
		} else {
			cb.mu.Unlock()
			return nil, ErrCircuitOpen
		}
	}

	cb.mu.Unlock()

	result, err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failures++
		cb.lastFailureAt = time.Now()
		if cb.failures >= cb.maxFailures {
			cb.state = StateOpen
		}
		return nil, err
	}

	// Success — reset
	cb.failures = 0
	cb.state = StateClosed
	return result, nil
}

func (cb *CircuitBreaker) State() CircuitState {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if cb.state == StateOpen && time.Since(cb.lastFailureAt) > cb.timeout {
		return StateHalfOpen
	}
	return cb.state
}
