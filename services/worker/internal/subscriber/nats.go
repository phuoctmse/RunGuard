package subscriber

import (
	"fmt"
	"log/slog"

	"github.com/nats-io/nats.go"
)

// Config holds NATS subscriber configuration.
type Config struct {
	URL     string
	Subject string
	Stream  string
}

// Subscriber manages a NATS JetStream connection and message subscription.
type Subscriber struct {
	config Config
	conn   *nats.Conn
	js     nats.JetStreamContext
}

// NewSubscriber creates a new Subscriber with defaults for empty config fields.
func NewSubscriber(cfg Config) *Subscriber {
	if cfg.Subject == "" {
		cfg.Subject = "incidents.new"
	}
	if cfg.Stream == "" {
		cfg.Stream = "INCIDENTS"
	}
	return &Subscriber{config: cfg}
}

// Connect establishes a NATS connection and ensures the JetStream stream exists.
func (s *Subscriber) Connect() error {
	nc, err := nats.Connect(s.config.URL)
	if err != nil {
		return fmt.Errorf("connect to NATS: %w", err)
	}
	s.conn = nc

	js, err := nc.JetStream()
	if err != nil {
		return fmt.Errorf("get JetStream context: %w", err)
	}
	s.js = js

	// Ensure stream exists
	_, err = js.AddStream(&nats.StreamConfig{
		Name:     s.config.Stream,
		Subjects: []string{s.config.Subject},
	})
	if err != nil {
		slog.Warn("stream may already exist", "error", err)
	}

	return nil
}

// Subscribe registers a handler for new incident messages.
// The handler receives raw message bytes.
func (s *Subscriber) Subscribe(handler func(data []byte)) error {
	_, err := s.js.Subscribe(s.config.Subject, func(msg *nats.Msg) {
		handler(msg.Data)
		if ackErr := msg.Ack(); ackErr != nil {
			slog.Error("failed to ack message", "error", ackErr)
		}
	}, nats.Durable("worker"), nats.ManualAck())
	if err != nil {
		return fmt.Errorf("subscribe to %s: %w", s.config.Subject, err)
	}
	return nil
}

// Close closes the NATS connection.
func (s *Subscriber) Close() {
	if s.conn != nil {
		s.conn.Close()
	}
}
