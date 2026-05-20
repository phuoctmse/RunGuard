import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { setToken } from '../api/client';

export default function LoginPage() {
  const [token, setTokenValue] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = token.trim();
    if (!trimmed) {
      setError('Token is required');
      return;
    }
    setToken(trimmed);
    navigate('/');
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>RunGuard</h2>
        <p className="login-subtitle">Enter your JWT token to continue</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="token">Authorization Token</label>
            <textarea
              id="token"
              value={token}
              onChange={(e) => {
                setTokenValue(e.target.value);
                setError('');
              }}
              placeholder="Paste your JWT token here..."
              rows={4}
            />
          </div>

          {error && <div className="error">{error}</div>}

          <button type="submit" className="btn btn-primary login-btn">
            Connect
          </button>
        </form>

        <div className="login-help">
          <p>Generate a token with:</p>
          <code>JWT_SECRET=your-secret ./scripts/gen-token.sh</code>
        </div>
      </div>
    </div>
  );
}
