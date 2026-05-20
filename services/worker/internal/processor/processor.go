package processor

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Config holds the processor configuration.
type Config struct {
	BackendURL string
}

// Processor forwards incident payloads to the backend API.
type Processor struct {
	config Config
	client *http.Client
}

// New creates a new Processor with the given config.
func New(cfg Config) *Processor {
	return &Processor{
		config: cfg,
		client: &http.Client{Timeout: 30 * time.Second},
	}
}

// HandleIncident forwards an incident payload to the backend API via POST.
func (p *Processor) HandleIncident(payload []byte) error {
	url := p.config.BackendURL + "/api/incidents"

	resp, err := p.client.Post(url, "application/json", bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("post to backend: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("backend returned %d: %s", resp.StatusCode, string(body))
	}

	return nil
}
