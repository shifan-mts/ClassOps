import React from 'react';

export default function LandingPage({ onSignIn, isSyncing }) {
  return (
    <div className="app landing">
      <header className="landing-header">
        <div>
          <p className="kicker">Teacher Workflow Automation</p>
          <h1>ClassOps</h1>
          <p className="subtitle">Keep syllabus targets, compliance metrics, and AI tools in one focused workspace.</p>
        </div>
        <button className="primary" onClick={onSignIn} disabled={isSyncing}>
          {isSyncing ? "Connecting..." : "Sign in with Google"}
        </button>
      </header>

      <section className="landing-hero">
        <div className="card landing-copy">
          <h2>Bring your teaching operations into one cockpit.</h2>
          <p>Sync Google Classroom, track syllabus targets, generate NBA/NAAC reports, and run AI tools without jumping between tabs.</p>
          <div className="landing-actions">
            <button className="primary" onClick={onSignIn} disabled={isSyncing}>
              {isSyncing ? "Connecting..." : "Continue with Google"}
            </button>
            <p className="landing-note">We only request Classroom data needed for your dashboard.</p>
          </div>
        </div>
        <div className="card landing-preview">
          <h3>NBA/NAAC Reports</h3>
          <p>We provide well-documented NBA/NAAC reports with CO/PO mapping and compliance-ready exports.</p>
        </div>
      </section>

      <section className="landing-grid">
        <div className="card">
          <h3>Syllabus Targets</h3>
          <p>Plan unit coverage, assign due dates, and mark completion in one place.</p>
        </div>
        <div className="card">
          <h3>Compliance Exports</h3>
          <p>Generate NBA/NAAC-ready reports with CO/PO mapping snapshots.</p>
        </div>
        <div className="card">
          <h3>AI Tools & Attendance</h3>
          <p>Check submissions, generate question papers, and keep attendance in sync.</p>
        </div>
      </section>
    </div>
  );
}
