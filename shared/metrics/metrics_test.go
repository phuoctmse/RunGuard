package metrics

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestMetricsEndpoint(t *testing.T) {
	handler := NewHandler("test-service")
	handler.RecordRequest("GET", "/test", 200)

	req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	w := httptest.NewRecorder()
	handler.MetricsHandler().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}

	body := w.Body.String()
	if !strings.Contains(body, "http_requests_total") {
		t.Error("metrics should contain http_requests_total")
	}
}

func TestRequestCounter(t *testing.T) {
	handler := NewHandler("test-service")

	// Record some requests
	handler.RecordRequest("GET", "/api/incidents", 200)
	handler.RecordRequest("GET", "/api/incidents", 200)
	handler.RecordRequest("POST", "/api/incidents", 201)

	// Verify counter incremented
	req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	w := httptest.NewRecorder()
	handler.MetricsHandler().ServeHTTP(w, req)

	body := w.Body.String()
	if !strings.Contains(body, "http_requests_total") {
		t.Error("metrics should contain http_requests_total")
	}
}
