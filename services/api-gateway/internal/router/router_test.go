package router

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRouterHealthz(t *testing.T) {
	r := NewRouter("http://localhost:8081", "")
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}
}

func TestRouterVersionedRoutes(t *testing.T) {
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	r := NewRouter(backend.URL, "")

	tests := []struct {
		path   string
		expect int
	}{
		{"/v1/incidents", http.StatusOK},
		{"/v1/runbooks", http.StatusOK},
		{"/healthz", http.StatusOK},
	}

	for _, tt := range tests {
		req := httptest.NewRequest(http.MethodGet, tt.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Code != tt.expect {
			t.Errorf("%s: status = %d, want %d", tt.path, w.Code, tt.expect)
		}
	}
}

func TestRouterOldApiPathReturns404(t *testing.T) {
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	r := NewRouter(backend.URL, "")
	req := httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("/api/incidents: status = %d, want %d", w.Code, http.StatusNotFound)
	}
}

func TestRouterInjectsServiceToken(t *testing.T) {
	var receivedToken string
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		receivedToken = r.Header.Get("X-Service-Token")
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	r := NewRouter(backend.URL, "test-token-123")
	req := httptest.NewRequest(http.MethodGet, "/v1/incidents", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	if receivedToken != "test-token-123" {
		t.Errorf("expected token %q, got %q", "test-token-123", receivedToken)
	}
}
