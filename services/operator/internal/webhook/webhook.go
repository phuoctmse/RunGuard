package webhook

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/phuoctmse/runguard/shared/types"
)

// AlertmanagerWebhook represents the incoming Alertmanager webhook payload.
type AlertmanagerWebhook struct {
	Alerts []Alert `json:"alerts"`
}

// Alert represents a single alert from Alertmanager.
type Alert struct {
	Status       string            `json:"status"`
	Labels       map[string]string `json:"labels"`
	Annotations  map[string]string `json:"annotations"`
	StartsAt     string            `json:"startsAt"`
	EndsAt       string            `json:"endsAt"`
}

// ParseWebhook parses an Alertmanager webhook request into an Incident.
func ParseWebhook(r *http.Request) (*types.Incident, error) {
	if r.Method != http.MethodPost {
		return nil, fmt.Errorf("expected POST, got %s", r.Method)
	}

	var wh AlertmanagerWebhook
	if err := json.NewDecoder(r.Body).Decode(&wh); err != nil {
		return nil, fmt.Errorf("decode webhook: %w", err)
	}

	if len(wh.Alerts) == 0 {
		return nil, fmt.Errorf("no alerts in webhook")
	}

	alert := wh.Alerts[0]
	inc := &types.Incident{
		AlertName: alert.Labels["alertname"],
		Severity:  alert.Labels["severity"],
		Namespace: alert.Labels["namespace"],
		Workload:  alert.Labels["workload"],
		Phase:     types.PhasePending,
	}

	if inc.AlertName == "" {
		return nil, fmt.Errorf("missing alertname label")
	}

	return inc, nil
}
