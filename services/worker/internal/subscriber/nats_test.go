package subscriber

import (
	"testing"
)

func TestSubscriberConfig(t *testing.T) {
	s := NewSubscriber(Config{
		URL:     "nats://localhost:4222",
		Subject: "incidents.new",
		Stream:  "INCIDENTS",
	})

	if s.config.Subject != "incidents.new" {
		t.Errorf("subject = %q, want %q", s.config.Subject, "incidents.new")
	}
	if s.config.Stream != "INCIDENTS" {
		t.Errorf("stream = %q, want %q", s.config.Stream, "INCIDENTS")
	}
}

func TestSubscriberConfigDefaults(t *testing.T) {
	s := NewSubscriber(Config{URL: "nats://localhost:4222"})

	if s.config.Subject != "incidents.new" {
		t.Errorf("default subject = %q, want %q", s.config.Subject, "incidents.new")
	}
	if s.config.Stream != "INCIDENTS" {
		t.Errorf("default stream = %q, want %q", s.config.Stream, "INCIDENTS")
	}
}
