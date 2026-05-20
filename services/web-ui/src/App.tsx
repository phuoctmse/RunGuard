import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import IncidentList from './components/IncidentList';
import IncidentDetail from './components/IncidentDetail';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<IncidentList />} />
          <Route path="incidents/:id" element={<IncidentDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
