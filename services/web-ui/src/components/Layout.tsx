import { Link, Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div style={{ fontFamily: 'system-ui', maxWidth: 960, margin: '0 auto', padding: 20 }}>
      <nav style={{ display: 'flex', gap: 16, marginBottom: 24, borderBottom: '1px solid #ddd', paddingBottom: 12 }}>
        <Link to="/" style={{ fontWeight: 700, fontSize: 20 }}>RunGuard</Link>
        <Link to="/">Incidents</Link>
      </nav>
      <Outlet />
    </div>
  );
}
