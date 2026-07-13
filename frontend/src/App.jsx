import { useState } from 'react';
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar isCollapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
        <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
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
