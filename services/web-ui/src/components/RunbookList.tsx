import { useEffect, useState } from 'react';
import { fetchRunbooks } from '../api/client';
import type { Runbook } from '../types';

export default function RunbookList() {
  const [runbooks, setRunbooks] = useState<Runbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRunbooks()
      .then(setRunbooks)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Unknown error'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading runbooks...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Runbooks</h2>
      </div>

      {runbooks.length === 0 ? (
        <div className="empty-state">No runbooks found</div>
      ) : (
        <div className="card-grid">
          {runbooks.map((rb, i) => (
            <div key={rb.id ?? i} className="card">
              <h3 className="card-title">{rb.alertName}</h3>
              <div className="card-meta">
                {rb.severity.map((s) => (
                  <span key={s} className={`severity severity-${s.toLowerCase()}`}>
                    {s}
                  </span>
                ))}
              </div>
              <div className="card-section">
                <h4>Diagnosis ({rb.diagnosis.length} steps)</h4>
                <ul>
                  {rb.diagnosis.map((step, j) => (
                    <li key={j}>{step.name}</li>
                  ))}
                </ul>
              </div>
              <div className="card-section">
                <h4>Remediation ({rb.remediation.length} steps)</h4>
                <ul>
                  {rb.remediation.map((step, j) => (
                    <li key={j}>
                      {step.name}
                      {step.autoApproved && <span className="badge badge-info">auto</span>}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
