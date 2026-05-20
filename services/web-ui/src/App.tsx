import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { getToken } from './api/client';
import Layout from './components/Layout';
import IncidentList from './components/IncidentList';
import IncidentDetail from './components/IncidentDetail';
import RunbookList from './components/RunbookList';
import LoginPage from './components/LoginPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!getToken()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<IncidentList />} />
          <Route path="incidents/:id" element={<IncidentDetail />} />
          <Route path="runbooks" element={<RunbookList />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
