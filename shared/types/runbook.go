package types

type DiagnosisStep struct {
	Name    string `json:"name"`
	Command string `json:"command"`
}

type RemediationStep struct {
	Name        string `json:"name"`
	Action      string `json:"action"`
	Target      string `json:"target"`
	Risk        string `json:"risk"`
	AutoApprove bool   `json:"autoApproved"`
}

type Runbook struct {
	AlertName   string            `json:"alertName"`
	Severity    []string          `json:"severity"`
	Diagnosis   []DiagnosisStep   `json:"diagnosis"`
	Remediation []RemediationStep `json:"remediation"`
	Rollback    []RemediationStep `json:"rollback"`
}
