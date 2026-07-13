import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  Building2,
  FileText,
  Settings,
  BarChart3,
  Brain,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export default function Sidebar({ isCollapsed, onToggle }) {
  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <button className="sidebar-toggle" onClick={onToggle} aria-label="Toggle Sidebar">
        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Brain size={22} />
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Main</div>
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
          <LayoutDashboard size={18} />
          <span className="nav-link-text">Dashboard</span>
        </NavLink>
        <NavLink to="/query" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <MessageSquare size={18} />
          <span className="nav-link-text">Ask Puddy</span>
        </NavLink>
        <NavLink to="/companies" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Building2 size={18} />
          <span className="nav-link-text">Companies</span>
        </NavLink>

        <div className="nav-section-label">Tools</div>
        <NavLink to="/resume" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileText size={18} />
          <span className="nav-link-text">Resume Analyzer</span>
        </NavLink>
        <NavLink to="/eval" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <BarChart3 size={18} />
          <span className="nav-link-text">Eval Dashboard</span>
        </NavLink>

        <div className="nav-section-label">System</div>
        <NavLink to="/admin" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Settings size={18} />
          <span className="nav-link-text">Admin</span>
        </NavLink>
      </nav>
    </aside>
  );
}
