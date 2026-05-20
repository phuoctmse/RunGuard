import { approveIncident, rejectIncident } from '../api/client';

interface Props {
  id: string;
  onDone: () => void;
}

export default function ApproveReject({ id, onDone }: Props) {
  const handleApprove = async () => {
    await approveIncident(id);
    onDone();
  };

  const handleReject = async () => {
    await rejectIncident(id);
    onDone();
  };

  return (
    <div style={{ display: 'flex', gap: 8, margin: '16px 0' }}>
      <button onClick={handleApprove} style={{ background: '#10b981', color: 'white', padding: '8px 16px', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
        Approve
      </button>
      <button onClick={handleReject} style={{ background: '#ef4444', color: 'white', padding: '8px 16px', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
        Reject
      </button>
    </div>
  );
}
