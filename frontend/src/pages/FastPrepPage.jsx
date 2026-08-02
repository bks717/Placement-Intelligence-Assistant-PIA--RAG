import { useState, useRef } from 'react';
import {
  Zap, Loader2, Upload, FileText, Building2, CalendarDays,
  Flame, ClipboardList, ExternalLink, BookOpen, Code2, Info,
  ChevronRight, Gauge,
} from 'lucide-react';
import api from '../services/api';

// Companies we have interview data for — quick picks
const SUGGESTIONS = ['ProcDNA', 'Walmart', 'Amazon', 'Infosys'];

// Study intensity — how much of the syllabus + DSA bank to cover
const LEVELS = [
  { id: 'simple', label: 'Simple', hint: 'Basics only — a quick brush-up' },
  { id: 'medium', label: 'Medium', hint: 'Basics + intermediate — solid coverage' },
  { id: 'hard', label: 'Hard', hint: 'Everything, basics → advanced — full grind' },
];

const PRIORITY_COLOR = {
  high: 'var(--accent-rose)',
  medium: 'var(--accent-amber)',
  low: 'var(--text-muted)',
};

const DIFF_COLOR = {
  Easy: 'var(--accent-emerald)',
  Medium: 'var(--accent-amber)',
  Hard: 'var(--accent-rose)',
};

export default function FastPrepPage() {
  const [company, setCompany] = useState('');
  const [jdFile, setJdFile] = useState(null);
  const [daysLeft, setDaysLeft] = useState(14);
  const [level, setLevel] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [plan, setPlan] = useState(null);
  const [tab, setTab] = useState('plan'); // 'plan' | 'questions'
  const fileRef = useRef(null);

  async function handleSubmit(e) {
    e?.preventDefault();
    if (loading) return;
    if (!company.trim() && !jdFile) {
      setError('Enter a company name or upload a JD PDF (at least one).');
      return;
    }
    setLoading(true);
    setError('');
    setPlan(null);
    try {
      const data = await api.getFastPrepPlan({
        company: company.trim(),
        daysLeft,
        level,
        jdFile,
      });
      setPlan(data);
      setTab('plan');
    } catch (err) {
      setError(err.message || 'Could not build a study plan.');
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setPlan(null);
    setError('');
  }

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Fast Prep</h1>
        <p className="page-subtitle">
          Tell us the company and/or drop the JD, plus how many days you have —
          get a day-by-day plan of exactly what to study and the questions seniors got asked.
        </p>
      </div>

      <div className="page-body">
        {/* ── Input form ── */}
        {!plan && !loading && (
          <form className="fp-form" onSubmit={handleSubmit}>
            <div className="fp-form-row">
              <label className="fp-field">
                <span className="fp-label"><Building2 size={14} /> Company</span>
                <input
                  className="fp-input"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. ProcDNA, Walmart, Amazon…"
                  autoFocus
                />
                <div className="fp-suggestions">
                  {SUGGESTIONS.map((s) => (
                    <button type="button" key={s} className="fp-chip" onClick={() => setCompany(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </label>

              <label className="fp-field">
                <span className="fp-label"><FileText size={14} /> Job Description PDF <em>(optional)</em></span>
                <div
                  className={`fp-drop ${jdFile ? 'fp-drop-has' : ''}`}
                  onClick={() => fileRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const f = e.dataTransfer.files[0];
                    if (f && f.name.toLowerCase().endsWith('.pdf')) setJdFile(f);
                  }}
                >
                  {jdFile ? (
                    <>
                      <FileText size={22} />
                      <span className="fp-drop-name">{jdFile.name}</span>
                      <span className="fp-drop-sub">{(jdFile.size / 1024).toFixed(0)} KB · click to replace</span>
                    </>
                  ) : (
                    <>
                      <Upload size={22} />
                      <span className="fp-drop-name">Drop JD PDF or click</span>
                      <span className="fp-drop-sub">helps tailor the plan to the exact role</span>
                    </>
                  )}
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".pdf"
                    style={{ display: 'none' }}
                    onChange={(e) => { if (e.target.files[0]) setJdFile(e.target.files[0]); }}
                  />
                </div>
              </label>
            </div>

            <label className="fp-field">
              <span className="fp-label">
                <CalendarDays size={14} /> Days left — <strong>{daysLeft}</strong> {daysLeft === 1 ? 'day' : 'days'}
              </span>
              <input
                className="fp-slider"
                type="range"
                min={1}
                max={60}
                value={daysLeft}
                onChange={(e) => setDaysLeft(Number(e.target.value))}
              />
              <div className="fp-slider-scale">
                <span>1</span><span>15</span><span>30</span><span>45</span><span>60</span>
              </div>
            </label>

            <div className="fp-field">
              <span className="fp-label">
                <Gauge size={14} /> How hard do you want to go?
              </span>
              <div className="fp-levels">
                {LEVELS.map((lv) => (
                  <button
                    type="button"
                    key={lv.id}
                    className={`fp-level ${level === lv.id ? 'fp-level-active' : ''}`}
                    onClick={() => setLevel(lv.id)}
                  >
                    <span className="fp-level-name">{lv.label}</span>
                    <span className="fp-level-hint">{lv.hint}</span>
                  </button>
                ))}
              </div>
            </div>

            {error && <div className="fp-error">{error}</div>}

            <button type="submit" className="btn btn-primary fp-submit" disabled={loading}>
              <Zap size={16} /> Build my study plan
            </button>
          </form>
        )}

        {/* ── Loading ── */}
        {loading && (
          <div className="fp-loading">
            <Loader2 size={40} className="about-spin" />
            <p>Building your <strong>{daysLeft}-day</strong> plan{company ? <> for <strong>{company}</strong></> : ''}…</p>
            <span className="fp-loading-hint">Pulling past interview questions and mapping out each day.</span>
          </div>
        )}

        {/* ── Plan ── */}
        {plan && !loading && (
          <div className="fp-result">
            {/* Header */}
            <div className="fp-result-head">
              <div>
                <div className="fp-result-company">{plan.company}</div>
                <div className="fp-result-meta">
                  {plan.role} · {plan.days_left} days · <span className="fp-density">{plan.density}</span>
                  <span className="fp-level-badge">Level: {plan.level || 'medium'}</span>
                  {plan.rounds?.length > 0 && <> · Rounds: {plan.rounds.join(' → ')}</>}
                </div>
              </div>
              <button className="btn btn-secondary" onClick={reset}>← New plan</button>
            </div>

            {plan.note && (
              <div className="fp-note"><Info size={15} /> <span>{plan.note}</span></div>
            )}

            {/* Tabs */}
            <div className="fp-tabs">
              <button
                className={`fp-tab ${tab === 'plan' ? 'fp-tab-active' : ''}`}
                onClick={() => setTab('plan')}
              >
                <ClipboardList size={15} /> Study Plan
              </button>
              <button
                className={`fp-tab ${tab === 'questions' ? 'fp-tab-active' : ''}`}
                onClick={() => setTab('questions')}
              >
                <Flame size={15} /> Top Asked
                {plan.interview_questions?.length > 0 && (
                  <span className="fp-tab-count">{plan.interview_questions.length}</span>
                )}
              </button>
            </div>

            {/* ── Study Plan tab ── */}
            {tab === 'plan' && (
              <div className="fp-tabpanel">
                {/* Core concepts */}
                {plan.core_concepts?.length > 0 && (
                  <section className="fp-section">
                    <h3 className="fp-section-title">
                      <BookOpen size={16} /> Core concepts to master
                      <span className="fp-section-count">
                        {plan.core_concepts.length} subjects ·{' '}
                        {plan.core_concepts.reduce((n, b) => n + b.concepts.length, 0)} concepts
                      </span>
                    </h3>
                    <div className="fp-concept-grid">
                      {plan.core_concepts.map((b, i) => (
                        <div key={i} className="fp-concept-bucket">
                          <div className="fp-bucket-head">
                            <span className="fp-bucket-name">{b.bucket}</span>
                            <span className="fp-bucket-pri" style={{ color: PRIORITY_COLOR[b.priority] || 'var(--text-muted)' }}>
                              {b.priority}
                            </span>
                          </div>
                          {b.why && <p className="fp-bucket-why">{b.why}</p>}
                          <div className="fp-concept-pills">
                            {b.concepts.map((c, j) => (
                              <a key={j} href={c.link} target="_blank" rel="noopener noreferrer" className="fp-concept-pill">
                                {c.name} <ExternalLink size={11} />
                              </a>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* DSA */}
                {plan.dsa?.length > 0 && (
                  <section className="fp-section">
                    <h3 className="fp-section-title">
                      <Code2 size={16} /> DSA — exact problems
                      <span className="fp-section-count">
                        {plan.dsa.reduce((n, p) => n + p.problems.length, 0)} problems ·{' '}
                        {plan.dsa.length} patterns
                      </span>
                    </h3>
                    <div className="fp-dsa-list">
                      {plan.dsa.map((pat, i) => (
                        <div key={i} className="fp-dsa-pattern">
                          <div className="fp-dsa-pattern-name">{pat.pattern}</div>
                          <ul className="fp-dsa-problems">
                            {pat.problems.map((p, j) => (
                              <li key={j}>
                                <a href={p.link} target="_blank" rel="noopener noreferrer" className="fp-dsa-problem">
                                  <span className="fp-diff-dot" style={{ background: DIFF_COLOR[p.difficulty] || 'var(--text-muted)' }} />
                                  <span className="fp-dsa-problem-name">{p.name}</span>
                                  <span className="fp-dsa-diff">{p.difficulty}</span>
                                  <ExternalLink size={12} />
                                </a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Day-by-day schedule */}
                {plan.schedule?.length > 0 && (
                  <section className="fp-section">
                    <h3 className="fp-section-title"><CalendarDays size={16} /> Day-by-day schedule</h3>
                    <div className="fp-schedule">
                      {plan.schedule.map((d) => (
                        <div key={d.day} className="fp-day">
                          <div className="fp-day-num">Day {d.day}</div>
                          <div className="fp-day-body">
                            <div className="fp-day-focus">{d.focus}</div>
                            {d.concepts?.length > 0 && (
                              <div className="fp-day-line"><ChevronRight size={12} /> <strong>Concepts:</strong> {d.concepts.join(', ')}</div>
                            )}
                            {d.dsa?.length > 0 && (
                              <div className="fp-day-line"><ChevronRight size={12} /> <strong>DSA:</strong> {d.dsa.join(', ')}</div>
                            )}
                            {d.revise_questions?.length > 0 && (
                              <div className="fp-day-line fp-day-revise">
                                <Flame size={12} /> <strong>Revise:</strong> {d.revise_questions.join(' · ')}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            )}

            {/* ── Top Asked tab ── */}
            {tab === 'questions' && (
              <div className="fp-tabpanel">
                {plan.interview_questions?.length > 0 ? (
                  <div className="fp-questions">
                    {plan.interview_questions.map((q, i) => (
                      <div key={i} className="fp-question">
                        <div className="fp-q-rank">#{i + 1}</div>
                        <div className="fp-q-body">
                          <div className="fp-q-text">{q.question}</div>
                          <div className="fp-q-meta">
                            <span className="fp-q-freq"><Flame size={12} /> asked in {q.asked_in} {q.asked_in === 1 ? 'write-up' : 'write-ups'}</span>
                            <span className="fp-q-round">{q.round}</span>
                            {q.source?.file && (
                              <span className="fp-q-src"><FileText size={11} /> {q.source.file} · p{q.source.page}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="fp-empty">
                    <Flame size={40} />
                    <h3>No past questions yet</h3>
                    <p>We don't have ingested interview write-ups for this company. Follow the Study Plan tab meanwhile.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
