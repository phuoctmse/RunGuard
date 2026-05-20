export type IncidentPhase =
  | 'Pending'
  | 'Analyzing'
  | 'RequiresApproval'
  | 'Executing'
  | 'Resolved'
  | 'Failed'
  | 'Rejected';

export interface Incident {
  id?: string;
  alertName: string;
  severity: string;
  namespace: string;
  workload: string;
  phase: IncidentPhase;
}

export interface AuditRecord {
  incident_id: string;
  type: string;
  timestamp: string;
  actor?: string;
  details?: Record<string, string>;
}

export interface DiagnosisStep {
  name: string;
  command: string;
}

export interface RemediationStep {
  name: string;
  action: string;
  target: string;
  risk: string;
  autoApproved: boolean;
}

export interface Runbook {
  id?: string;
  alertName: string;
  severity: string[];
  diagnosis: DiagnosisStep[];
  remediation: RemediationStep[];
  rollback: RemediationStep[];
}
