import React from 'react';

const AIToolsPanel = ({
  isQuotaExceeded,
  customApiKey,
  setCustomApiKey,
  updateServerKey,
  selectedCourseId,
  setSelectedCourseId,
  courses,
  qPaperTopic,
  setQPaperTopic,
  qpOutput,
  setQpOutput,
  generatePaper,
  isGenerating,
  error,
  docLink,
  generatedPaper,
  syncAssignments,
  isSyncing,
  selectedAssignmentId,
  setSelectedAssignmentId,
  assignments,
  analyzeSubmissions,
  isAnalyzing,
  analysisData,
  aiError,
  setAiFile,
  handleAiCheck,
  aiLoading,
  aiResult
}) => {
  return (
    <section className="stack">
      <div className="card">
        <div className="card-header">
          <h3>Bloom's Taxonomy Question Paper Generator</h3>
          <p>Generate balanced questions with CO mapping and cognitive levels.</p>
        </div>
        <div className="card-body">
          {isQuotaExceeded && (
            <div className="input-row" style={{ marginBottom: '12px' }}>
              <input
                style={{ flex: 1 }}
                type="password"
                placeholder="Enter Gemini API Key (Required: Server credits low)"
                value={customApiKey}
                onChange={(e) => setCustomApiKey(e.target.value)}
              />
              <button className="ghost" onClick={updateServerKey}>Update Server Key</button>
            </div>
          )}
          <div className="input-row">
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              style={{ width: '200px' }}
            >
              <option value="">Select Subject</option>
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <input
              style={{ flex: 1 }}
              placeholder="Enter topic (e.g., Operating Systems)"
              value={qPaperTopic}
              onChange={(e) => setQPaperTopic(e.target.value)}
            />
            <select
              value={qpOutput}
              onChange={(e) => setQpOutput(e.target.value)}
              style={{ width: '180px' }}
            >
              <option value="google_doc">Google Doc</option>
              <option value="docx">Download DOCX</option>
              <option value="text">Preview Text</option>
            </select>
            <button className="primary" onClick={generatePaper} disabled={!qPaperTopic || isGenerating}>
              {isGenerating ? "Generating..." : "Generate"}
            </button>
          </div>
          {error && (
            <div style={{ marginTop: '12px', padding: '12px', background: '#fff5f5', border: '1px solid #feb2b2', borderRadius: '6px' }}>
              <p className="error" style={{ margin: 0, color: '#c53030' }}>⚠️ {error}</p>
              {isQuotaExceeded && (
                <p style={{ fontSize: '13px', marginTop: '8px', color: '#742a2a' }}>
                  <b>Action Required:</b> Please enter your own Gemini API Key in the box above to continue.
                </p>
              )}
            </div>
          )}
          {docLink && (
            <div className="output" style={{ marginTop: '12px' }}>
              <a href={docLink} target="_blank" rel="noreferrer">Open Google Doc</a>
            </div>
          )}
          {generatedPaper && (
            <div className="output" style={{ whiteSpace: 'pre-wrap', textAlign: 'left', fontFamily: 'monospace' }}>
              {generatedPaper}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Classroom Plagiarism & AI Analysis</h3>
          <p>Select an assignment to cross-check all student submissions for similarity and AI patterns.</p>
        </div>
        <div className="card-body">
          <div className="input-row">
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              style={{ width: '200px' }}
            >
              <option value="">Select Subject</option>
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button className="ghost sm" onClick={syncAssignments} disabled={isSyncing}>
              {isSyncing ? "Syncing..." : "Sync Assignments"}
            </button>
          </div>

          <div className="input-row" style={{ marginTop: '12px' }}>
            <select
              style={{ flex: 1 }}
              value={selectedAssignmentId}
              onChange={(e) => setSelectedAssignmentId(e.target.value)}
            >
              <option value="">Select Assignment</option>
              {assignments.map(a => (
                <option key={a.id} value={a.id}>{a.title}</option>
              ))}
            </select>
            <button className="primary" onClick={analyzeSubmissions} disabled={!selectedAssignmentId || isAnalyzing}>
              {isAnalyzing ? "Analyzing..." : "Analyze All Submissions"}
            </button>
          </div>
          
          {isAnalyzing && <p style={{ marginTop: '12px' }}>Analyzing submissions... this may take a moment.</p>}
          
          {analysisData && (
            <div style={{ marginTop: '20px' }}>
              <table className="attendance-table">
                <thead>
                  <tr>
                    <th>Student Name</th>
                    <th style={{ textAlign: 'right' }}>AI Score</th>
                    <th style={{ textAlign: 'right' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisData.results.map((r, idx) => (
                    <tr key={idx}>
                      <td>{r.name}</td>
                      <td style={{ textAlign: 'right' }}>{r.ai_score}%</td>
                      <td style={{ textAlign: 'right' }}>{r.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: '24px' }}>
                <h4 style={{ marginBottom: '12px', color: '#334155' }}>Plagiarism Check (100% Match Rule)</h4>
                <table className="attendance-table">
                  <thead>
                    <tr>
                      <th>Student Name</th>
                      <th style={{ textAlign: 'right' }}>Match %</th>
                      <th style={{ textAlign: 'right' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisData.plagiarism && analysisData.plagiarism.map((p, idx) => (
                      <tr key={idx}>
                        <td>
                          {p.name}
                          {p.matched_with !== 'N/A' && <div style={{ fontSize: '11px', color: '#64748b' }}>Matched with: {p.matched_with}</div>}
                        </td>
                        <td style={{ textAlign: 'right' }}>{p.score}%</td>
                        <td style={{ textAlign: 'right', color: p.status.includes('❌') ? '#dc2626' : 'inherit', fontWeight: p.status.includes('❌') ? 'bold' : 'normal' }}>
                          {p.status}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {analysisData.alerts && analysisData.alerts.length > 0 && (
                <div style={{ marginTop: '15px', padding: '12px', background: '#fff5f5', border: '1px solid #feb2b2', borderRadius: '6px' }}>
                  <h4 style={{ color: '#c53030', marginTop: 0 }}>🚩 Plagiarism Alerts</h4>
                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                    {analysisData.alerts.map((a, idx) => (
                      <li key={idx} style={{ color: '#c53030' }}>
                        Match between <b>{a.students[0]}</b> and <b>{a.students[1]}</b> ({a.score}% similarity)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          {aiError && <p className="error">{aiError}</p>}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Manual File AI Check</h3>
          <p>Upload a PDF or DOCX to measure AI content usage for a single file.</p>
        </div>
        <div className="card-body">
          <div className="input-row">
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => setAiFile(e.target.files?.[0] || null)}
            />
            <button className="primary" onClick={handleAiCheck} disabled={aiLoading}>
              {aiLoading ? "Analyzing..." : "Analyze File"}
            </button>
          </div>
          {aiResult && !isAnalyzing && (
            <div className="output">
              {aiResult}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default AIToolsPanel;
