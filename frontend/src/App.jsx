import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import SplashLoader from './components/SplashLoader';
import Dashboard from './pages/Dashboard';
import QueryPage from './pages/QueryPage';
import CompaniesPage from './pages/CompaniesPage';
import CompanyDetailPage from './pages/CompanyDetailPage';
import ResumePage from './pages/ResumePage';
import EvalPage from './pages/EvalPage';
import AdminPage from './pages/AdminPage';

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [splashLoading, setSplashLoading] = useState(true);
  const [splashFadeOut, setSplashFadeOut] = useState(false);

  useEffect(() => {
    // Stage 1: trigger fade out at 2200ms
    const fadeTimer = setTimeout(() => setSplashFadeOut(true), 2200);
    // Stage 2: completely unmount at 2700ms (after 500ms CSS opacity transition)
    const mountTimer = setTimeout(() => setSplashLoading(false), 2700);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(mountTimer);
    };
  }, []);

  if (splashLoading) {
    return <SplashLoader fadeOut={splashFadeOut} />;
  }

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
