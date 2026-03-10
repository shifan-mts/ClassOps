import React, { useState } from 'react';
import './App.css';
import Timetablegenerator from './components/ui/page/Timetablegenerator';

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [qPaperTopic, setQPaperTopic] = useState("");
  const [generatedPaper, setGeneratedPaper] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");

  const handleGoogleSync = () => {
    window.location.href = "http://localhost:5000/api/auth/google";
  };

  const generatePaper = async () => {
    setError("");
    setGeneratedPaper("");
    setIsGenerating(true);
    try {
      const res = await fetch("http://localhost:5000/api/question-paper/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: qPaperTopic, difficulty: "Hard" })
      });
      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`);
      }
      const data = await res.json();
      const content = data?.question_paper || data?.questionPaper || "No question paper returned.";
      setGeneratedPaper(content);
    } catch (err) {
      setError("Could not generate the question paper. Check the backend server and try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="kicker">Teacher Workflow Automation</p>
          <h1>EduSync OS</h1>
          <p className="subtitle">Keep syllabus targets, compliance metrics, and AI tools in one focused workspace.</p>
        </div>
        <button className="primary" onClick={handleGoogleSync}>
          Sync with Google Classroom
        </button>
      </header>

      <div className="tabs">
        <div className="tab-list" role="tablist" aria-label="Dashboard Sections">
          {[
            { id: "overview", label: "Overview & Targets" },
            { id: "attendance", label: "Attendance" },
            { id: "ai-tools", label: "AI Tools" },
            { id: "timetable", label: "Timetable" }
          ].map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "overview" && (
          <section className="grid">
            <div className="card">
              <div className="card-header">
                <h3>Material & Target Completion</h3>
                <p>Track progress by unit and upcoming deadlines.</p>
              </div>
              <div className="card-body">
                <ul className="list">
                  <li>
                    <span>Unit 1: Data Structures</span>
                    <span className="status success">Completed</span>
                  </li>
                  <li>
                    <span>Unit 2: Algorithms</span>
                    <span className="status warn">Pending (Due: Oct 12)</span>
                  </li>
                </ul>
                <button className="ghost">+ Add Syllabus Target</button>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>NBA/NAAC Metrics Data</h3>
                <p>Export mapped CO & PO outcomes for compliance.</p>
              </div>
              <div className="card-body">
                <div className="metric-grid">
                  <div>
                    <p className="metric-label">CO Coverage</p>
                    <p className="metric-value">84%</p>
                  </div>
                  <div>
                    <p className="metric-label">PO Mapping</p>
                    <p className="metric-value">92%</p>
                  </div>
                  <div>
                    <p className="metric-label">Last Export</p>
                    <p className="metric-value">Mar 6</p>
                  </div>
                </div>
                <button className="primary full">Generate NBA Compliance Report</button>
              </div>
            </div>
          </section>
        )}

        {activeTab === "ai-tools" && (
          <section className="stack">
            <div className="card">
              <div className="card-header">
                <h3>Bloom's Taxonomy Question Paper Generator</h3>
                <p>Generate balanced questions aligned to cognitive levels.</p>
              </div>
              <div className="card-body">
                <div className="input-row">
                  <input
                    placeholder="Enter topic (e.g., Operating Systems)"
                    value={qPaperTopic}
                    onChange={(e) => setQPaperTopic(e.target.value)}
                  />
                  <button className="primary" onClick={generatePaper} disabled={!qPaperTopic || isGenerating}>
                    {isGenerating ? "Generating..." : "Generate"}
                  </button>
                </div>
                {error && <p className="error">{error}</p>}
                {generatedPaper && (
                  <div className="output">
                    {generatedPaper}
                  </div>
                )}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>Plagiarism & Originality Check</h3>
                <p>Upload drafts and measure similarity against previous submissions.</p>
              </div>
              <div className="card-body">
                <div className="placeholder">
                  Connect to your submissions archive to enable plagiarism checks.
                </div>
              </div>
            </div>
          </section>
        )}

        {activeTab === "attendance" && (
          <section className="stack">
            <div className="card">
              <div className="card-header">
                <h3>Attendance Tracker</h3>
                <p>Log presence, export summaries, and flag chronic absences.</p>
              </div>
              <div className="card-body">
                <div className="placeholder">
                  Attendance tracker UI goes here.
                </div>
              </div>
            </div>
          </section>
        )}

        {activeTab === "timetable" && (
          <section className="stack">
            <Timetablegenerator />
          </section>
        )}
      </div>
    </div>
  );
}
