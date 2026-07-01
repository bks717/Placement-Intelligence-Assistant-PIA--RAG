import { useState, useEffect, useRef } from 'react';
import { Upload, FileText, CheckCircle2, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function ResumePage() {
  const [company, setCompany] = useState('');
  const [companies, setCompanies] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    api.getCompanies().then(data => {
      setCompanies(data.companies || []);
    }).catch(() => {});
  }, []);

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.name.endsWith('.pdf')) {
      setFile(droppedFile);
    }
  }

  function handleFileSelect(e) {
    const selected = e.target.files[0];
    if (selected) setFile(selected);
  }

  async function handleAnalyze() {
    if (!company) { setError('Please select a target company'); return; }
    if (!file) { setError('Please upload your resume PDF'); return; }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await api.analyzeResume(company, file);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function getScoreColor(score) {
    if (score >= 80) return 'var(--accent-emerald)';
    if (score >= 50) return 'var(--accent-amber)';
    return 'var(--accent-rose)';
  }

  function getScoreGradient(score) {
    if (score >= 80) return 'conic-gradient(var(--accent-emerald) calc(var(--pct) * 1%), var(--border-color) 0)';
    if (score >= 50) return 'conic-gradient(var(--accent-amber) calc(var(--pct) * 1%), var(--border-color) 0)';
    return 'conic-gradient(var(--accent-rose) calc(var(--pct) * 1%), var(--border-color) 0)';
  }

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Resume Analyzer</h1>
        <p className="page-subtitle">Compare your resume against a company's job description</p>
      </div>

      <div className="page-body">
        <div className="resume-layout">
          {/* Left: Upload */}
          <div>
            <div className="card" style={{ marginBottom: 16 }}>
              <h3 className="card-title" style={{ marginBottom: 16 }}>Upload Resume</h3>

              <div
                className={`upload-zone ${dragOver ? 'dragover' : ''}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                {file ? (
                  <>
                    <FileText size={48} style={{ color: 'var(--accent-emerald)' }} />
                    <div className="upload-zone-text">{file.name}</div>
                    <div className="upload-zone-sub">{(file.size / 1024).toFixed(1)} KB</div>
                  </>
                ) : (
                  <>
                    <Upload size={48} />
                    <div className="upload-zone-text">Drop your resume PDF here</div>
                    <div className="upload-zone-sub">or click to browse</div>
                  </>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </div>

            <div className="card">
              <h3 className="card-title" style={{ marginBottom: 16 }}>Target Company</h3>
              <select
                className="filter-select"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                style={{ width: '100%', marginBottom: 16 }}
              >
                <option value="">Select a company...</option>
                {companies.map(c => (
                  <option key={c.company} value={c.company}>{c.company}</option>
                ))}
              </select>

              {error && (
                <div style={{
                  padding: '8px 12px',
                  background: 'var(--accent-rose-dim)',
                  color: 'var(--accent-rose)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 13,
                  marginBottom: 16,
                }}>
                  {error}
                </div>
              )}

              <button
                className="btn btn-primary"
                style={{ width: '100%' }}
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Analyzing...</> : 'Analyze Resume'}
              </button>
            </div>
          </div>

          {/* Right: Results */}
          <div>
            {result ? (
              <>
                {/* Score Circle */}
                <div className="card" style={{ marginBottom: 16, textAlign: 'center' }}>
                  <div className="match-score">
                    <div
                      className="match-score-circle"
                      style={{
                        background: getScoreGradient(result.match_score),
                        '--pct': result.match_score,
                        color: getScoreColor(result.match_score),
                      }}
                    >
                      <span>{result.match_score}%</span>
                    </div>
                    <div className="match-score-label">
                      Match Score for {result.company} — {result.role}
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'center', gap: 24, fontSize: 13 }}>
                    <span><strong style={{ color: 'var(--accent-emerald)' }}>{result.matched_skills?.length || 0}</strong> matched</span>
                    <span><strong style={{ color: 'var(--accent-rose)' }}>{result.missing_skills?.length || 0}</strong> missing</span>
                    <span><strong style={{ color: 'var(--accent-amber)' }}>{result.extra_skills?.length || 0}</strong> extra</span>
                  </div>
                </div>

                {/* Skills Lists */}
                <div style={{ display: 'grid', gap: 16 }}>
                  {result.matched_skills?.length > 0 && (
                    <div className="card">
                      <h3 className="card-title" style={{ marginBottom: 12, color: 'var(--accent-emerald)' }}>
                        <CheckCircle2 size={16} style={{ display: 'inline', marginRight: 6 }} />
                        Matched Skills
                      </h3>
                      <div className="skills-list">
                        {result.matched_skills.map((s, i) => (
                          <div key={i} className="skill-item matched">{s}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.missing_skills?.length > 0 && (
                    <div className="card">
                      <h3 className="card-title" style={{ marginBottom: 12, color: 'var(--accent-rose)' }}>
                        <XCircle size={16} style={{ display: 'inline', marginRight: 6 }} />
                        Missing Skills
                      </h3>
                      <div className="skills-list">
                        {result.missing_skills.map((s, i) => (
                          <div key={i} className="skill-item missing">{s}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.recommendations?.length > 0 && (
                    <div className="card">
                      <h3 className="card-title" style={{ marginBottom: 12, color: 'var(--accent-amber)' }}>
                        <AlertTriangle size={16} style={{ display: 'inline', marginRight: 6 }} />
                        Recommendations
                      </h3>
                      <div className="skills-list">
                        {result.recommendations.map((r, i) => (
                          <div key={i} className="skill-item extra">{r}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="empty-state">
                  <FileText size={64} />
                  <h3 className="empty-state-title">Upload & Analyze</h3>
                  <p className="empty-state-text">
                    Upload your resume and select a target company to see your skill gap analysis.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
