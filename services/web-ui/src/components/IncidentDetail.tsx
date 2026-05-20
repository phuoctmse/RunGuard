import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { fetchIncident } from '../api/client';
import type { Incident } from '../types';
import ApproveReject from './ApproveReject';
import Timeline from './Timeline';

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    fetchIncident(id).then(setIncident).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p>Loading...</p>;
  if (!incident) return <p>Incident not found</p>;

  return (
    <div>
      <h2>{incident.alertName}</h2>
      <dl>
        <dt>Namespace</dt><dd>{incident.namespace}</dd>
        <dt>Workload</dt><dd>{incident.workload}</dd>
        <dt>Severity</dt><dd>{incident.severity}</dd>
        <dt>Phase</dt><dd>{incident.phase}</dd>
      </dl>

      {incident.phase === 'RequiresApproval' && id && (
        <ApproveReject id={id} onDone={() => fetchIncident(id).then(setIncident)} />
      )}

      {id && <Timeline incidentId={id} />}
    </div>
  );
}
