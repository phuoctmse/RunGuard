package resilience

import (
	"errors"
	"testing"
	"time"
)

func TestRetrySucceedsFirstAttempt(t *testing.T) {
	attempts := 0
	err := Retry(3, 10*time.Millisecond, func() error {
		attempts++
		return nil
	})

	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if attempts != 1 {
		t.Errorf("expected 1 attempt, got %d", attempts)
	}
}

func TestRetrySucceedsAfterFailures(t *testing.T) {
	attempts := 0
	err := Retry(3, 10*time.Millisecond, func() error {
		attempts++
		if attempts < 3 {
			return errors.New("temporary failure")
		}
		return nil
	})

	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if attempts != 3 {
		t.Errorf("expected 3 attempts, got %d", attempts)
	}
}

func TestRetryExhaustsAllAttempts(t *testing.T) {
	attempts := 0
	err := Retry(3, 10*time.Millisecond, func() error {
		attempts++
		return errors.New("permanent failure")
	})

	if err == nil {
		t.Error("expected error after exhausting retries")
	}
	if attempts != 3 {
		t.Errorf("expected 3 attempts, got %d", attempts)
	}
}

func TestRetryExponentialBackoff(t *testing.T) {
	attempts := 0
	start := time.Now()
	_ = Retry(3, 50*time.Millisecond, func() error {
		attempts++
		return errors.New("fail")
	})
	elapsed := time.Since(start)

	// Backoff: 0ms + 50ms + 100ms = 150ms minimum
	if elapsed < 140*time.Millisecond {
		t.Errorf("expected ~150ms backoff, got %v", elapsed)
	}
	if attempts != 3 {
		t.Errorf("expected 3 attempts, got %d", attempts)
	}
}
