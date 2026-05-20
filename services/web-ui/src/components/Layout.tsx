import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { clearToken } from '../api/client';

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();

  const navLink = (to: string, label: string) => (
    <Link
      to={to}
      className={`nav-link ${location.pathname === to ? 'active' : ''}`}
    >
      {label}
    </Link>
  );

  const handleLogout = () => {
    clearToken();
    navigate('/login');
  };

  return (
    <div className="app">
      <nav className="navbar">
        <Link to="/" className="brand">RunGuard</Link>
        <div className="nav-links">
          {navLink('/', 'Incidents')}
          {navLink('/runbooks', 'Runbooks')}
        </div>
        <div className="nav-spacer" />
        <button onClick={handleLogout} className="btn btn-secondary btn-sm">
          Logout
        </button>
      </nav>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
