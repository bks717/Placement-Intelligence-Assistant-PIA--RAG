import { Zap } from 'lucide-react';

/**
 * Fast Prep — quick-fire placement prep.
 * Placeholder for now — the user will come back to build this out.
 */
export default function FastPrepPage() {
  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Fast Prep</h1>
        <p className="page-subtitle">Quick-fire practice to sharpen your skills</p>
      </div>

      <div className="page-body">
        <div className="empty-state">
          <Zap size={64} />
          <h3 className="empty-state-title">Coming soon</h3>
          <p className="empty-state-text">
            Fast Prep is on the way — quick practice questions, mini-tests and
            rapid revision will land here.
          </p>
        </div>
      </div>
    </>
  );
}
