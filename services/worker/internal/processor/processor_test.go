package processor

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestProcessorHandleIncident(t *testing.T) {
	var received bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		received = true
		if r.Method != http.MethodPost {
			t.Errorf("method = %q, want POST", r.Method)
		}
		if r.URL.Path != "/api/incidents" {
			t.Errorf("path = %q, want /api/incidents", r.URL.Path)
		}
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(map[string]string{"id": "inc-1"})
	}))
	defer server.Close()

	p := New(Config{BackendURL: server.URL})
	err := p.HandleIncident([]byte(`{"alertName":"PodCrashLooping","namespace":"production","workload":"api-server"}`))
	if err != nil {
		t.Fatalf("HandleIncident failed: %v", err)
	}

	if !received {
		t.Error("backend did not receive the incident")
	}
}

func TestProcessorHandleIncidentBackendDown(t *testing.T) {
	p := New(Config{BackendURL: "http://localhost:1"})
	err := p.HandleIncident([]byte(`{"alertName":"test"}`))
	if err == nil {
		t.Error("expected error when backend is down")
	}
}

func TestProcessorHandleIncidentInvalidJSON(t *testing.T) {
	// Invalid JSON is still valid bytes to post - the processor forwards raw bytes.
	// This test verifies the processor does not crash on arbitrary byte payloads.
	// The backend (not the processor) is responsible for JSON validation.
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusCreated)
	}))
	defer server.Close()

	p := New(Config{BackendURL: server.URL})
	err := p.HandleIncident([]byte(`not json`))
	if err != nil {
		t.Errorf("processor should forward raw bytes without error: %v", err)
	}
}
