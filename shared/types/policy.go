package types

type Scope struct {
	Namespace []string `json:"namespace"`
	Resources []string `json:"resources"`
}

type BlastRadius struct {
	MaxPodsAffected       int  `json:"maxPodsAffected"`
	MaxNamespacesAffected int  `json:"maxNamespacesAffected"`
	ForbidDelete          bool `json:"forbidDelete"`
}

type ApprovalConfig struct {
	RequireApprovalFor []string `json:"requireApprovalFor"`
	Approvers          []string `json:"approvers"`
	TimeoutMinutes     int      `json:"timeoutMinutes"`
}

type Policy struct {
	Scope       Scope          `json:"scope"`
	BlastRadius BlastRadius    `json:"blastRadius"`
	Approval    ApprovalConfig `json:"approval"`
	Forbidden   []string       `json:"forbidden"`
}
