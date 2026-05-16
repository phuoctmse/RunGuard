package notify

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Notifier defines the notification interface.
type Notifier interface {
	NotifyApprovalNeeded(incidentID, alertName, actionSummary, reason string) error
	NotifyApproved(incidentID, approver string) error
	NotifyRejected(incidentID, rejector, reason string) error
	NotifyFailed(incidentID, errorMsg string) error
}

// SlackPayload is the Slack Block Kit message format.
type SlackPayload struct {
	Blocks []SlackBlock `json:"blocks"`
}

type SlackBlock struct {
	Type string     `json:"type"`
	Text *SlackText `json:"text,omitempty"`
}

type SlackText struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

// SlackNotifier sends notifications via Slack webhook.
type SlackNotifier struct {
	webhookURL string
	client     *http.Client
}

func NewSlackNotifier(webhookURL string) *SlackNotifier {
	return &SlackNotifier{
		webhookURL: webhookURL,
		client:     &http.Client{Timeout: 10 * time.Second},
	}
}

func (n *SlackNotifier) NotifyApprovalNeeded(incidentID, alertName, actionSummary, reason string) error {
	payload := SlackPayload{
		Blocks: []SlackBlock{
			{
				Type: "header",
				Text: &SlackText{Type: "plain_text", Text: "⚠️ Approval Required"},
			},
			{
				Type: "section",
				Text: &SlackText{
					Type: "mrkdwn",
					Text: fmt.Sprintf(
						"*Incident:* %s\n*Alert:* %s\n*Action:* %s\n*Reason:* %s",
						incidentID, alertName, actionSummary, reason,
					),
				},
			},
			{
				Type: "section",
				Text: &SlackText{
					Type: "mrkdwn",
					Text: fmt.Sprintf(
						"Approve: `POST /api/incidents/%s/approve`\nReject: `POST /api/incidents/%s/reject`",
						incidentID, incidentID,
					),
				},
			},
		},
	}
	return n.send(payload)
}

func (n *SlackNotifier) NotifyApproved(incidentID, approver string) error {
	payload := SlackPayload{
		Blocks: []SlackBlock{
			{
				Type: "section",
				Text: &SlackText{
					Type: "mrkdwn",
					Text: fmt.Sprintf("✅ Incident *%s* approved by %s", incidentID, approver),
				},
			},
		},
	}
	return n.send(payload)
}

func (n *SlackNotifier) NotifyRejected(incidentID, rejector, reason string) error {
	payload := SlackPayload{
		Blocks: []SlackBlock{
			{
				Type: "section",
				Text: &SlackText{
					Type: "mrkdwn",
					Text: fmt.Sprintf("❌ Incident *%s* rejected by %s\nReason: %s", incidentID, rejector, reason),
				},
			},
		},
	}
	return n.send(payload)
}

func (n *SlackNotifier) NotifyFailed(incidentID, errorMsg string) error {
	payload := SlackPayload{
		Blocks: []SlackBlock{
			{
				Type: "section",
				Text: &SlackText{
					Type: "mrkdwn",
					Text: fmt.Sprintf("🔴 Incident *%s* failed\nError: %s", incidentID, errorMsg),
				},
			},
		},
	}
	return n.send(payload)
}

func (n *SlackNotifier) send(payload SlackPayload) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal payload: %w", err)
	}

	resp, err := n.client.Post(n.webhookURL, "application/json", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("send webhook: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("webhook returned status %d", resp.StatusCode)
	}

	return nil
}
