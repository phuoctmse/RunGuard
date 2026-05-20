
import { useState } from 'react';
import { approveIncident, rejectIncident } from '../api/client';

interface Props {
  id: string;
  onDone: () => void;
}

export default function ApproveReject({ id, onDone }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApprove = async () => {
    setLoading(true);
    setError(null);
    try {
      await approveIncident(id);
      onDone();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to approve');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    setLoading(true);
    setError(null);
    try {
      await rejectIncident(id);
      onDone();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to reject');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="approval-section">
      <h3>Approval Required</h3>
      <p>This incident is waiting for approval to proceed with remediation.</p>
      {error && <div className="error">{error}</div>}
      <div className="approval-actions">
        <button
          onClick={handleApprove}
          disabled={loading}
          className="btn btn-success"
        >
          {loading ? 'Processing...' : 'Approve'}
        </button>
        <button
          onClick={handleReject}
          disabled={loading}
          className="btn btn-danger"
        >
          {loading ? 'Processing...' : 'Reject'}
        </button>
      </div>
    </div>
  );
}
