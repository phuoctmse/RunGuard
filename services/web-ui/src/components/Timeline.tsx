import { useEffect, useState } from 'react';
import { fetchAuditTrail } from '../api/client';
import type { AuditRecord } from '../types';

interface Props {
  incidentId: string;
}

export default function Timeline({ incidentId }: Props) {
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAuditTrail(incidentId)
      .then(setRecords)
      .finally(() => setLoading(false));
  }, [incidentId]);

  if (loading) return <div className="loading">Loading timeline...</div>;
  if (records.length === 0) return <div className="empty-state">No audit records</div>;

  return (
    <div className="timeline-section">
      <h3>Timeline</h3>
      <ul className="timeline">
        {records.map((r, i) => (
          <li key={i} className="timeline-item">
            <div className="timeline-marker" />
            <div className="timeline-content">
              <strong className="timeline-type">{r.type}</strong>
              <span className="timeline-time">
                {new Date(r.timestamp).toLocaleString()}
              </span>
              {r.actor && <span className="timeline-actor">by {r.actor}</span>}
              {r.details && (
                <pre className="timeline-details">
                  {JSON.stringify(r.details, null, 2)}
                </pre>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
