package webhook

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/phuoctmse/runguard/shared/types"
)

// AlertmanagerPayload represents an incoming Alertmanager webhook.
type AlertmanagerPayload struct {
	Alerts []Alert `json:"alerts"`
}

// Alert represents a single alert from Alertmanager.
type Alert struct {
	Status      string            `json:"status"`
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
}

// ParseWebhook extracts an Incident from an Alertmanager webhook request.
func ParseWebhook(r *http.Request) (*types.Incident, error) {
	var payload AlertmanagerPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		return nil, fmt.Errorf("invalid JSON: %w", err)
	}

	if len(payload.Alerts) == 0 {
		return nil, fmt.Errorf("no alerts in payload")
	}

	// Use the first firing alert
	alert := payload.Alerts[0]
	if alert.Status != "firing" {
		return nil, fmt.Errorf("alert status is %q, not firing", alert.Status)
	}

	return &types.Incident{
		AlertName: alert.Labels["alertname"],
		Severity:  alert.Labels["severity"],
		Namespace: alert.Labels["namespace"],
		Workload:  alert.Labels["pod"],
		Phase:     types.PhasePending,
	}, nil
}
