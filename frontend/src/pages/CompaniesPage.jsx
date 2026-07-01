import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, ArrowRight } from 'lucide-react';
import api from '../services/api';

export default function CompaniesPage() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.getCompanies().then(data => {
      setCompanies(data.companies || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <div className="page-header">
          <h1 className="page-title">Companies</h1>
        </div>
        <div className="page-body">
          <div className="loading-spinner"><div className="spinner"></div></div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Companies</h1>
        <p className="page-subtitle">Browse interview experiences and job descriptions by company</p>
      </div>

      <div className="page-body">
        {companies.length === 0 ? (
          <div className="empty-state">
            <Building2 size={64} />
            <h3 className="empty-state-title">No companies yet</h3>
            <p className="empty-state-text">
              Upload interview experience and JD documents in the Admin page to get started.
            </p>
          </div>
        ) : (
          <div className="companies-grid">
            {companies.map((c, i) => (
              <div
                key={i}
                className="company-card"
                onClick={() => navigate(`/companies/${c.company}`)}
              >
                <div className="company-name">{c.company}</div>
                <div className="company-role">{c.role}</div>
                {c.package !== 'Not mentioned' && (
                  <div className="company-package">{c.package}</div>
                )}
                {c.skills?.length > 0 && (
                  <div className="company-skills">
                    {c.skills.slice(0, 6).map((skill, j) => (
                      <span key={j} className="skill-tag">{skill}</span>
                    ))}
                    {c.skills.length > 6 && (
                      <span className="skill-tag">+{c.skills.length - 6}</span>
                    )}
                  </div>
                )}
                <div className="company-meta">
                  <span>{c.total_questions || 0} questions</span>
                  {c.rounds?.length > 0 && <span>{c.rounds.length} rounds</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
