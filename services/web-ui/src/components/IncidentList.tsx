import { useIncidents } from '../hooks/useIncidents';

const phaseColor: Record<string, string> = {
  Pending: '#6b7280',
  Analyzing: '#3b82f6',
  RequiresApproval: '#f59e0b',
  Executing: '#8b5cf6',
  Resolved: '#10b981',
  Failed: '#ef4444',
  Rejected: '#ef4444',
};

export default function IncidentList() {
  const { incidents, loading, error, refresh } = useIncidents();

  if (loading) return <div className="loading">Loading incidents...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Incidents</h2>
        <button onClick={refresh} className="btn btn-secondary">Refresh</button>
      </div>

      {incidents.length === 0 ? (
        <div className="empty-state">No incidents found</div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Alert</th>
                <th>Namespace</th>
                <th>Workload</th>
                <th>Severity</th>
                <th>Phase</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc, i) => (
                <tr key={inc.id ?? i}>
                  <td>{inc.alertName}</td>
                  <td><code>{inc.namespace}</code></td>
                  <td><code>{inc.workload}</code></td>
                  <td>
                    <span className={`severity severity-${inc.severity.toLowerCase()}`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td>
                    <span
                      className="phase-badge"
                      style={{ backgroundColor: phaseColor[inc.phase] || '#6b7280' }}
                    >
                      {inc.phase}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
