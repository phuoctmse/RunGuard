package webhook

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestParseAlertmanagerWebhook(t *testing.T) {
	payload := AlertmanagerPayload{
		Alerts: []Alert{
			{
				Status: "firing",
				Labels: map[string]string{
					"alertname": "PodCrashLooping",
					"severity":  "critical",
					"namespace": "production",
					"pod":       "api-server-xyz",
				},
			},
		},
	}

	body, _ := json.Marshal(payload)
	req := httptest.NewRequest(http.MethodPost, "/webhook/alertmanager", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")

	got, err := ParseWebhook(req)
	if err != nil {
		t.Fatalf("ParseWebhook failed: %v", err)
	}

	if got.AlertName != "PodCrashLooping" {
		t.Errorf("AlertName = %q, want %q", got.AlertName, "PodCrashLooping")
	}
	if got.Severity != "critical" {
		t.Errorf("Severity = %q, want %q", got.Severity, "critical")
	}
	if got.Namespace != "production" {
		t.Errorf("Namespace = %q, want %q", got.Namespace, "production")
	}
}

func TestParseWebhookInvalidJSON(t *testing.T) {
	req := httptest.NewRequest(http.MethodPost, "/webhook/alertmanager", bytes.NewReader([]byte("invalid")))
	_, err := ParseWebhook(req)
	if err == nil {
		t.Error("expected error for invalid JSON")
	}
}

func TestParseWebhookEmptyAlerts(t *testing.T) {
	payload := AlertmanagerPayload{Alerts: []Alert{}}
	body, _ := json.Marshal(payload)
	req := httptest.NewRequest(http.MethodPost, "/webhook/alertmanager", bytes.NewReader(body))

	_, err := ParseWebhook(req)
	if err == nil {
		t.Error("expected error for empty alerts")
	}
}
