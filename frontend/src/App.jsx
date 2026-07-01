import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import QueryPage from './pages/QueryPage';
import CompaniesPage from './pages/CompaniesPage';
import CompanyDetailPage from './pages/CompanyDetailPage';
import ResumePage from './pages/ResumePage';
import EvalPage from './pages/EvalPage';
import AdminPage from './pages/AdminPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/query" element={<QueryPage />} />
            <Route path="/companies" element={<CompaniesPage />} />
            <Route path="/companies/:name" element={<CompanyDetailPage />} />
            <Route path="/resume" element={<ResumePage />} />
            <Route path="/eval" element={<EvalPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
