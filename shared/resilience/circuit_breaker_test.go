package resilience

import (
	"errors"
	"testing"
	"time"
)

func TestCircuitBreakerOpensAfterFailures(t *testing.T) {
	cb := NewCircuitBreaker("test", 3, 1*time.Second)

	for range 3 {
		_, _ = cb.Execute(func() (any, error) {
			return nil, errors.New("service unavailable")
		})
	}

	if cb.State() != StateOpen {
		t.Errorf("expected circuit open, got %v", cb.State())
	}
}

func TestCircuitBreakerAllowsSuccess(t *testing.T) {
	cb := NewCircuitBreaker("test", 3, 1*time.Second)

	result, err := cb.Execute(func() (any, error) {
		return "ok", nil
	})

	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if result != "ok" {
		t.Errorf("expected 'ok', got %v", result)
	}
	if cb.State() != StateClosed {
		t.Errorf("expected circuit closed, got %v", cb.State())
	}
}

func TestCircuitBreakerResetsOnSuccess(t *testing.T) {
	cb := NewCircuitBreaker("test", 3, 100*time.Millisecond)

	// 2 failures (not enough to open)
	for range 2 {
		_, _ = cb.Execute(func() (any, error) {
			return nil, errors.New("fail")
		})
	}

	// Success resets the counter
	_, _ = cb.Execute(func() (any, error) {
		return "ok", nil
	})

	// 2 more failures should NOT open the circuit
	for range 2 {
		_, _ = cb.Execute(func() (any, error) {
			return nil, errors.New("fail")
		})
	}

	if cb.State() != StateClosed {
		t.Errorf("expected circuit closed after reset, got %v", cb.State())
	}
}

func TestCircuitBreakerRejectsWhenOpen(t *testing.T) {
	cb := NewCircuitBreaker("test", 2, 1*time.Second)

	// Open the circuit
	for range 2 {
		_, _ = cb.Execute(func() (any, error) {
			return nil, errors.New("fail")
		})
	}

	// Should reject immediately
	_, err := cb.Execute(func() (any, error) {
		t.Error("should not be called when circuit is open")
		return nil, nil
	})

	if err == nil {
		t.Error("expected error when circuit is open")
	}
}

func TestCircuitBreakerHalfOpenAfterTimeout(t *testing.T) {
	cb := NewCircuitBreaker("test", 2, 50*time.Millisecond)

	// Open the circuit
	for range 2 {
		_, _ = cb.Execute(func() (any, error) {
			return nil, errors.New("fail")
		})
	}

	// Wait for timeout
	time.Sleep(100 * time.Millisecond)

	// Should allow one request (half-open)
	result, err := cb.Execute(func() (any, error) {
		return "ok", nil
	})

	if err != nil {
		t.Errorf("unexpected error in half-open state: %v", err)
	}
	if result != "ok" {
		t.Errorf("expected 'ok', got %v", result)
	}
	if cb.State() != StateClosed {
		t.Errorf("expected circuit closed after half-open success, got %v", cb.State())
	}
}
