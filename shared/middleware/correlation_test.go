package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCorrelationIDMiddleware(t *testing.T) {
	var capturedID string

	handler := CorrelationID(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedID = GetCorrelationID(r.Context())
	}))

	// Request without X-Request-ID → should generate one
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	if capturedID == "" {
		t.Error("correlation ID should be generated")
	}
	if w.Header().Get("X-Request-ID") == "" {
		t.Error("X-Request-ID header should be set in response")
	}
}

func TestCorrelationIDPassthrough(t *testing.T) {
	var capturedID string

	handler := CorrelationID(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedID = GetCorrelationID(r.Context())
	}))

	// Request with X-Request-ID → should pass through
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("X-Request-ID", "existing-id-123")
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	if capturedID != "existing-id-123" {
		t.Errorf("expected existing ID, got %q", capturedID)
	}
}
