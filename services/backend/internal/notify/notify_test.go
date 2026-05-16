package notify

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestSlackNotification(t *testing.T) {
	var receivedBody string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		buf := make([]byte, r.ContentLength)
		_, _ = r.Body.Read(buf)
		receivedBody = string(buf)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	notifier := NewSlackNotifier(server.URL)

	err := notifier.NotifyApprovalNeeded("inc-1", "PodCrashLooping", "restart on api-server", "high risk action")
	if err != nil {
		t.Fatalf("NotifyApprovalNeeded failed: %v", err)
	}

	if receivedBody == "" {
		t.Error("no notification sent")
	}

	// Verify it's valid Slack payload
	var payload SlackPayload
	_ = json.Unmarshal([]byte(receivedBody), &payload)
	if len(payload.Blocks) == 0 {
		t.Error("Slack payload should have blocks")
	}
}

func TestSlackNotificationOnApproval(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	notifier := NewSlackNotifier(server.URL)

	err := notifier.NotifyApproved("inc-1", "user-1")
	if err != nil {
		t.Fatalf("NotifyApproved failed: %v", err)
	}
}

func TestSlackNotificationOnRejection(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	notifier := NewSlackNotifier(server.URL)

	err := notifier.NotifyRejected("inc-1", "user-1", "too risky")
	if err != nil {
		t.Fatalf("NotifyRejected failed: %v", err)
	}
}

func TestSlackNotificationOnFailure(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	notifier := NewSlackNotifier(server.URL)

	err := notifier.NotifyFailed("inc-1", "scale failed: timeout")
	if err != nil {
		t.Fatalf("NotifyFailed failed: %v", err)
	}
}

func TestSlackNotificationWebhookDown(t *testing.T) {
	// Test graceful handling when Slack is unreachable
	notifier := NewSlackNotifier("http://localhost:1") // invalid port

	err := notifier.NotifyApprovalNeeded("inc-1", "test", "test", "test")
	if err == nil {
		t.Error("expected error when webhook is unreachable")
	}
}
