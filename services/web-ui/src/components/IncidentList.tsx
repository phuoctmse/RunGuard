import { Link } from 'react-router-dom';
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
  const { incidents, loading, error } = useIncidents();

  if (loading) return <p>Loading...</p>;
  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

  return (
    <div>
      <h2>Incidents</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '2px solid #ddd' }}>
            <th>Alert</th>
            <th>Namespace</th>
            <th>Workload</th>
            <th>Severity</th>
            <th>Phase</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((inc, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
              <td><Link to={`/incidents/${i}`}>{inc.alertName}</Link></td>
              <td>{inc.namespace}</td>
              <td>{inc.workload}</td>
              <td>{inc.severity}</td>
              <td>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: 4,
                  backgroundColor: phaseColor[inc.phase] || '#6b7280',
                  color: 'white',
                  fontSize: 12,
                }}>
                  {inc.phase}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
