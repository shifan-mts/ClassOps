import React, { useState, useEffect } from 'react';
import './App.css';

const AttendanceReport = ({ courseId }) => {
  const [report, setReport] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchReport = async () => {
    if (!courseId) return;
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:5000/api/attendance/report/${courseId}`);
      const data = await res.json();
      setReport(data);
    } catch (err) {
      console.error("Failed to fetch report", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (courseId) fetchReport();
  }, [courseId]);

  return (
    <div className="card">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3>Attendance Report</h3>
          <p>Overall percentage for each student in this subject.</p>
        </div>
        <button className="ghost" onClick={fetchReport} disabled={loading}>
          {loading ? "Loading..." : "Generate Report"}
        </button>
      </div>
      <div className="card-body">
        {report.length > 0 ? (
          <table className="report-table">
            <thead>
              <tr>
                <th>Roll Number</th>
                <th>Name</th>
                <th>Present</th>
                <th>Total</th>
                <th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              {report.map((row) => (
                <tr key={row.student_id}>
                  <td>{row.roll_number}</td>
                  <td>{row.name}</td>
                  <td style={{ textAlign: 'center' }}>{row.present}</td>
                  <td style={{ textAlign: 'center' }}>{row.total}</td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={row.percentage < 75 ? "status warn-bg" : "status success-bg"}>
                      {row.percentage}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="placeholder">Click "Generate Report" to view summaries.</p>
        )}
      </div>
    </div>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [students, setStudents] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState({});
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [qPaperTopic, setQPaperTopic] = useState("");
  const [generatedPaper, setGeneratedPaper] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [syncError, setSyncError] = useState("");
  const [aiFile, setAiFile] = useState(null);
  const [aiResult, setAiResult] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");

  const API_BASE = "http://localhost:5000";

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/courses`);
      const data = await res.json();
      setCourses(Array.isArray(data) ? data : []);
      if (Array.isArray(data) && data.length > 0 && !selectedCourseId) {
        setSelectedCourseId(data[0].id.toString());
      }
    } catch (err) {
      console.error("Failed to fetch courses", err);
    }
  };

  const fetchStudents = async (courseId) => {
    if (!courseId) return;
    try {
      const res = await fetch(`${API_BASE}/api/courses/${courseId}/students`);
      const data = await res.json();
      setStudents(data);
      
      const initial = {};
      data.forEach(s => initial[s.id] = "Present");
      setAttendanceRecords(initial);
    } catch (err) {
      console.error("Failed to fetch students", err);
    }
  };

  const syncStudents = async () => {
    if (!selectedCourseId) return;
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/courses/${selectedCourseId}/sync-students`, {
        method: "POST"
      });
      if (res.ok) {
        fetchStudents(selectedCourseId);
        alert("Students synced successfully!");
      } else {
        const error = await res.json();
        alert(error.error || "Sync failed.");
      }
    } catch (err) {
      alert("Error syncing students");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleGoogleSync = () => {
    setSyncError("");
    setIsSyncing(true);
    fetch(`${API_BASE}/api/classroom/sync`, { credentials: "include" })
      .then(async (res) => {
        if (res.status === 401) {
          window.location.href = `${API_BASE}/api/auth/google`;
          return null;
        }
        if (!res.ok) {
          throw new Error("Sync failed");
        }
        return res.json();
      })
      .then((data) => {
        if (!data) return;
        setCourses(Array.isArray(data.courses) ? data.courses : []);
      })
      .catch(() => {
        setSyncError("Could not sync courses. Please try again.");
      })
      .finally(() => {
        setIsSyncing(false);
      });
  };

  useEffect(() => {
    if (selectedCourseId) {
      fetchStudents(selectedCourseId);
    }
  }, [selectedCourseId]);

  const handleAttendanceChange = (studentId, status) => {
    setAttendanceRecords(prev => ({ ...prev, [studentId]: status }));
  };

  const saveAttendance = async () => {
    try {
      const records = Object.entries(attendanceRecords).map(([id, status]) => ({
        student_id: parseInt(id),
        status
      }));
      
      await fetch("http://localhost:5000/api/attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          course_id: parseInt(selectedCourseId), 
          date: attendanceDate, 
          records 
        })
      });
      alert("Attendance saved!");
    } catch (err) {
      alert("Error saving attendance");
    }
  };

  const generatePaper = async () => {
    setGeneratedPaper("");
    setError("");
    setIsGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/question-paper/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: qPaperTopic, difficulty: "Hard" })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || `Request failed with status ${res.status}`);
      }
      const content = data?.question_paper || data?.questionPaper || "No question paper returned.";
      setGeneratedPaper(content);
    } catch (err) {
      setError(err?.message || "Could not generate the question paper. Check the backend server and try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAiCheck = async () => {
    setAiError("");
    setAiResult("");
    if (!aiFile) {
      setAiError("Please upload a PDF or DOCX file first.");
      return;
    }
    setAiLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", aiFile);
      const res = await fetch(`${API_BASE}/api/assignments/check`, {
        method: "POST",
        body: formData,
        credentials: "include"
      });
      const data = await res.json();
      if (!res.ok || data?.success === false) {
        throw new Error(data?.error || data?.message || "AI check failed");
      }
      const formatted = data?.formatted || data?.data || data;
      setAiResult(typeof formatted === "string" ? formatted : JSON.stringify(formatted, null, 2));
    } catch (err) {
      setAiError(err?.message || "Could not analyze the file. Please try again.");
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="kicker">Teacher Workflow Automation</p>
          <h1>ClassOps</h1>
          <p className="subtitle">Keep syllabus targets, compliance metrics, and AI tools in one focused workspace.</p>
        </div>
        <button className="primary" onClick={handleGoogleSync} disabled={isSyncing}>
          {isSyncing ? "Syncing..." : "Sync with Google Classroom"}
        </button>
      </header>

      <div className="tabs">
        <div className="tab-list">
          {[
            { id: "overview", label: "Overview & Targets" },
            { id: "attendance", label: "Attendance" },
            { id: "ai-tools", label: "AI Tools" },
            { id: "timetable", label: "Timetable" }
          ].map((tab) => (
            <button
              key={tab.id}
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
                </div>
                <button className="primary full">Generate NBA Compliance Report</button>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>Google Classroom Courses</h3>
                <p>Synced courses from your connected Google Classroom account.</p>
              </div>
              <div className="card-body">
                <button className="primary" onClick={handleGoogleSync} disabled={isSyncing}>
                  {isSyncing ? "Syncing..." : "Sync Courses"}
                </button>
                {syncError && <p className="error">{syncError}</p>}
                {courses.length > 0 ? (
                  <ul className="list">
                    {courses.map((course) => (
                      <li key={course.id || course.google_course_id}>
                        <span>{course.name}</span>
                        {course.google_course_id && (
                          <span className="status">{course.google_course_id}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="placeholder">
                    No courses loaded yet. Click "Sync Courses" to fetch them.
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {activeTab === "attendance" && (
          <section className="stack">
            <div className="card">
              <div className="card-header">
                <h3>Subject-wise Attendance</h3>
                <p>Log presence for the selected subject and date.</p>
              </div>
              <div className="card-body">
                <div className="input-row">
                  <select 
                    value={selectedCourseId}
                    onChange={(e) => setSelectedCourseId(e.target.value)}
                  >
                    <option value="">Select Subject</option>
                    {courses.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                  <input
                    type="date"
                    value={attendanceDate}
                    onChange={(e) => setAttendanceDate(e.target.value)}
                  />
                  <button className="ghost" onClick={syncStudents} disabled={isSyncing}>
                    {isSyncing ? "Syncing..." : "Sync Roster"}
                  </button>
                  <button className="primary" onClick={saveAttendance}>Save Attendance</button>
                </div>
                
                {students.length > 0 ? (
                  <table className="attendance-table">
                    <thead>
                      <tr>
                        <th>Roll Number</th>
                        <th>Name</th>
                        <th style={{ textAlign: 'right' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((s) => (
                        <tr key={s.id}>
                          <td>{s.roll_number}</td>
                          <td>{s.name}</td>
                          <td style={{ textAlign: 'right' }}>
                            <select
                              value={attendanceRecords[s.id] || "Present"}
                              onChange={(e) => handleAttendanceChange(s.id, e.target.value)}
                            >
                              <option value="Present">Present</option>
                              <option value="Absent">Absent</option>
                              <option value="Late">Late</option>
                            </select>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="placeholder">
                    No students found for this subject. Try "Sync Roster" to fetch from Google Classroom.
                  </div>
                )}
              </div>
            </div>

            <AttendanceReport courseId={parseInt(selectedCourseId)} />
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
                    style={{ flex: 1 }}
                    placeholder="Enter topic (e.g., Operating Systems)"
                    value={qPaperTopic}
                    onChange={(e) => setQPaperTopic(e.target.value)}
                  />
                  <button className="primary" onClick={generatePaper} disabled={!qPaperTopic || isGenerating}>
                    {isGenerating ? "Generating..." : "Generate"}
                  </button>
                </div>
                {generatedPaper && (
                  <div className="output">
                    {generatedPaper}
                  </div>
                )}
                {error && <p className="error">{error}</p>}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>Plagiarism & Originality Check</h3>
                <p>Upload a PDF or DOCX to measure AI content usage.</p>
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
                {aiError && <p className="error">{aiError}</p>}
                {aiResult && (
                  <div className="output">
                    {aiResult}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {activeTab === "timetable" && (
          <section className="stack">
            <div className="card">
              <div className="card-header">
                <h3>Timetable Planner</h3>
                <p>Visualize weekly slots and auto-assign available rooms.</p>
              </div>
              <div className="card-body">
                <div className="placeholder">
                  Timetable grid UI goes here. (Work in Progress)
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
