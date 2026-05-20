import { useEffect, useState } from 'react';
import { fetchAuditTrail } from '../api/client';
import type { AuditRecord } from '../types';

interface Props {
  incidentId: string;
}

export default function Timeline({ incidentId }: Props) {
  const [records, setRecords] = useState<AuditRecord[]>([]);

  useEffect(() => {
    fetchAuditTrail(incidentId).then(setRecords);
  }, [incidentId]);

  if (records.length === 0) return <p>No audit records</p>;

  return (
    <div>
      <h3>Timeline</h3>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {records.map((r, i) => (
          <li key={i} style={{ borderLeft: '2px solid #3b82f6', paddingLeft: 12, marginBottom: 12 }}>
            <strong>{r.type}</strong>
            <br />
            <small>{new Date(r.timestamp).toLocaleString()}</small>
            {r.actor && <span> — by {r.actor}</span>}
            {r.details && (
              <pre style={{ fontSize: 12, background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                {JSON.stringify(r.details, null, 2)}
              </pre>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
