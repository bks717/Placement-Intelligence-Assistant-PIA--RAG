import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  Building2,
  FileText,
  Settings,
  BarChart3,
  Brain,
} from 'lucide-react';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Brain size={22} />
          </div>
          <div>
            <div className="sidebar-logo-text">PIA</div>
            <div className="sidebar-logo-sub">Placement Intelligence</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Main</div>
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
          <LayoutDashboard size={18} />
          Dashboard
        </NavLink>
        <NavLink to="/query" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <MessageSquare size={18} />
          Ask PIA
        </NavLink>
        <NavLink to="/companies" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Building2 size={18} />
          Companies
        </NavLink>

        <div className="nav-section-label">Tools</div>
        <NavLink to="/resume" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileText size={18} />
          Resume Analyzer
        </NavLink>
        <NavLink to="/eval" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <BarChart3 size={18} />
          Eval Dashboard
        </NavLink>

        <div className="nav-section-label">System</div>
        <NavLink to="/admin" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Settings size={18} />
          Admin
        </NavLink>
      </nav>
    </aside>
  );
}
