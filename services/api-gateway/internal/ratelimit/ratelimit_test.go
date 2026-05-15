package ratelimit

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRateLimiterAllowsUnderLimit(t *testing.T) {
	limiter := New(10, 10) // 10 requests per second, burst 10

	for i := 0; i < 10; i++ {
		req := httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
		req.RemoteAddr = "192.168.1.1:12345"
		w := httptest.NewRecorder()

		called := false
		handler := limiter.Limit(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			called = true
		}))

		handler.ServeHTTP(w, req)

		if !called {
			t.Errorf("request %d: handler should have been called", i)
		}
	}
}

func TestRateLimiterBlocksOverLimit(t *testing.T) {
	limiter := New(1, 1) // 1 request per second, burst 1

	// First request should pass
	req := httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
	req.RemoteAddr = "192.168.1.1:12345"
	w := httptest.NewRecorder()
	limiter.Limit(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {})).ServeHTTP(w, req)

	// Second request should be rate limited
	req = httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
	req.RemoteAddr = "192.168.1.1:12345"
	w = httptest.NewRecorder()
	limiter.Limit(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called")
	})).ServeHTTP(w, req)

	if w.Code != http.StatusTooManyRequests {
		t.Errorf("status = %d, want %d", w.Code, http.StatusTooManyRequests)
	}
}
