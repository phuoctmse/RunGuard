package health

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthEndpoints(t *testing.T) {
	checker := New("test-service")
	checker.AddCheck("database", func() error { return nil })
	checker.AddCheck("nats", func() error { return nil })

	// Liveness
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	w := httptest.NewRecorder()
	checker.LiveHandler()(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("liveness: status = %d, want %d", w.Code, http.StatusOK)
	}

	// Readiness
	req = httptest.NewRequest(http.MethodGet, "/readyz", nil)
	w = httptest.NewRecorder()
	checker.ReadyHandler()(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("readiness: status = %d, want %d", w.Code, http.StatusOK)
	}
}

func TestReadinessFailsWhenCheckFails(t *testing.T) {
	checker := New("test-service")
	checker.AddCheck("database", func() error { return fmt.Errorf("connection refused") })

	req := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	w := httptest.NewRecorder()
	checker.ReadyHandler()(w, req)

	if w.Code != http.StatusServiceUnavailable {
		t.Errorf("readiness: status = %d, want %d", w.Code, http.StatusServiceUnavailable)
	}
}
