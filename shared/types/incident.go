package types

type IncidentPhase string

const (
	PhasePending          IncidentPhase = "Pending"
	PhaseAnalyzing        IncidentPhase = "Analyzing"
	PhaseRequiresApproval IncidentPhase = "RequiresApproval"
	PhaseExecuting        IncidentPhase = "Executing"
	PhaseResolved         IncidentPhase = "Resolved"
	PhaseFailed           IncidentPhase = "Failed"
	PhaseRejected         IncidentPhase = "Rejected"
)

type Incident struct {
	AlertName string        `json:"alertName"`
	Severity  string        `json:"severity"`
	Namespace string        `json:"namespace"`
	Workload  string        `json:"workload"`
	Phase     IncidentPhase `json:"phase"`
}

type ProposedAction struct {
	Action string `json:"action"`
	Target string `json:"target"`
	Reason string `json:"reason"`
	Risk   string `json:"risk"`
}
