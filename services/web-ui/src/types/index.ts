export type IncidentPhase =
  | 'Pending'
  | 'Analyzing'
  | 'RequiresApproval'
  | 'Executing'
  | 'Resolved'
  | 'Failed'
  | 'Rejected';

export interface Incident {
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
