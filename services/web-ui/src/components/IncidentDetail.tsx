import { useParams } from 'react-router-dom';
import { useEffect, useState, useCallback } from 'react';
import { fetchIncident } from '../api/client';
import type { Incident } from '../types';
import ApproveReject from './ApproveReject';
import Timeline from './Timeline';

const phaseColor: Record<string, string> = {
  Pending: '#6b7280',
  Analyzing: '#3b82f6',
  RequiresApproval: '#f59e0b',
  Executing: '#8b5cf6',
  Resolved: '#10b981',
  Failed: '#ef4444',
  Rejected: '#ef4444',
};

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const data = await fetchIncident(id);
      setIncident(data);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load incident');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <div className="loading">Loading incident...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!incident) return <div className="empty-state">Incident not found</div>;

  return (
    <div>
      <div className="page-header">
        <h2>{incident.alertName}</h2>
        <span
          className="phase-badge"
          style={{ backgroundColor: phaseColor[incident.phase] || '#6b7280' }}
        >
          {incident.phase}
        </span>
      </div>

      <div className="detail-grid">
        <div className="detail-card">
          <h3>Details</h3>
          <dl className="detail-list">
            <dt>Namespace</dt>
            <dd><code>{incident.namespace}</code></dd>
            <dt>Workload</dt>
            <dd><code>{incident.workload}</code></dd>
            <dt>Severity</dt>
            <dd>
              <span className={`severity severity-${incident.severity.toLowerCase()}`}>
                {incident.severity}
              </span>
            </dd>
          </dl>
        </div>
      </div>

      {incident.phase === 'RequiresApproval' && id && (
        <ApproveReject id={id} onDone={load} />
      )}

      {id && <Timeline incidentId={id} />}
    </div>
  );
}
