import React, { useState, useEffect } from 'react';
import './App.css';
import Timetablegenerator from './components/ui/page/Timetablegenerator';

function AttendanceReport({ courseId }) {
  const [report, setReport] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (courseId) {
      fetchReport();
    }
  }, [courseId]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:5000/api/attendance/report/${courseId}`);
      const data = await res.json();
      setReport(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch report", err);
    } finally {
      setLoading(false);
    }
  };

  if (!courseId) return null;

  return (
    <div className="card">
      <div className="card-header">
        <h3>Attendance Report</h3>
        <p>Overall percentage for all students in this subject.</p>
      </div>
      <div className="card-body">
        {loading ? (
          <p>Loading report...</p>
        ) : report.length > 0 ? (
          <table className="attendance-table">
            <thead>
              <tr>
                <th>Roll Number</th>
                <th>Name</th>
                <th>Attendance</th>
              </tr>
            </thead>
            <tbody>
              {report.map((item) => (
                <tr key={item.student_id}>
                  <td>{item.roll_number}</td>
                  <td>{item.name}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div className="progress-bar" style={{ flex: 1, height: '8px', background: '#e2e8f0', borderRadius: '4px' }}>
                        <div style={{
                          width: `${item.percentage}%`,
                          height: '100%',
                          background: item.percentage > 75 ? '#22c55e' : item.percentage > 50 ? '#f59e0b' : '#ef4444',
                          borderRadius: '4px'
                        }} />
                      </div>
                      <span>{item.percentage}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="placeholder">No attendance records found yet.</div>
        )}
      </div>
    </div>
  );
}

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
  const [aiCourseId, setAiCourseId] = useState("");
  const [courseworkItems, setCourseworkItems] = useState([]);
  const [courseworkLoading, setCourseworkLoading] = useState(false);
  const [selectedCourseworkId, setSelectedCourseworkId] = useState("");
  const [plagiarismResults, setPlagiarismResults] = useState([]);
  const [plagiarismLoading, setPlagiarismLoading] = useState(false);
  const [plagiarismError, setPlagiarismError] = useState("");

  const API_BASE = "http://localhost:5000";

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/courses`, { credentials: "include" });
      const data = await res.json();
      setCourses(Array.isArray(data) ? data : []);
      if (Array.isArray(data) && data.length > 0 && !selectedCourseId) {
        setSelectedCourseId(data[0].id.toString());
      }
    } catch (err) {
      console.error("Failed to fetch courses", err);
    }
  };

  const fetchCoursework = async (courseId) => {
    if (!courseId) return;
    setCourseworkLoading(true);
    setPlagiarismError("");
    setCourseworkItems([]);
    setSelectedCourseworkId("");
    try {
      const res = await fetch(`${API_BASE}/api/classroom/courses/${courseId}/coursework`, { credentials: "include" });
      const data = await res.json();
      if (res.status === 403 && data?.reauth) {
        window.location.href = `${API_BASE}/api/auth/google`;
        return;
      }
      if (!res.ok) {
        throw new Error(data?.error || "Failed to load assignments");
      }
      const list = Array.isArray(data) ? data : [];
      setCourseworkItems(list);
      if (list.length > 0) {
        setSelectedCourseworkId(list[0].id);
      }
    } catch (err) {
      setPlagiarismError(err?.message || "Could not load assignments.");
    } finally {
      setCourseworkLoading(false);
    }
  };

  const runPlagiarismCheck = async () => {
    if (!aiCourseId || !selectedCourseworkId) {
      setPlagiarismError("Select a classroom and assignment first.");
      return;
    }
    setPlagiarismLoading(true);
    setPlagiarismError("");
    setPlagiarismResults([]);
    try {
      const res = await fetch(`${API_BASE}/api/classroom/courses/${aiCourseId}/coursework/${selectedCourseworkId}/plagiarism`, {
        method: "POST",
        credentials: "include"
      });
      const data = await res.json();
      if (res.status === 403 && data?.reauth) {
        window.location.href = `${API_BASE}/api/auth/google`;
        return;
      }
      if (!res.ok) {
        throw new Error(data?.error || "Plagiarism check failed.");
      }
      setPlagiarismResults(Array.isArray(data?.results) ? data.results : []);
    } catch (err) {
      setPlagiarismError(err?.message || "Plagiarism check failed.");
    } finally {
      setPlagiarismLoading(false);
    }
  };

  useEffect(() => {
    if (courses.length > 0 && !aiCourseId) {
      setAiCourseId(courses[0].id.toString());
    }
  }, [courses]);

  useEffect(() => {
    if (aiCourseId) {
      fetchCoursework(aiCourseId);
    } else {
      setCourseworkItems([]);
      setSelectedCourseworkId("");
    }
  }, [aiCourseId]);

  const fetchStudents = async (courseId) => {
    if (!courseId) return;
    try {
      const res = await fetch(`${API_BASE}/api/courses/${courseId}/students`, { credentials: "include" });
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
        method: "POST",
        credentials: "include"
      });
      if (res.status === 401) {
        window.location.href = `${API_BASE}/api/auth/google`;
        return;
      }
      const payload = await res.json();
      if (res.ok) {
        fetchStudents(selectedCourseId);
        const count = payload?.count ?? 0;
        alert(`Students synced successfully! (${count})`);
        if (count === 0) {
          alert("No students returned from Google Classroom. Check the People tab or re-sync OAuth scopes.");
        }
      } else {
        alert(payload?.error || "Sync failed.");
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

      const res = await fetch("http://localhost:5000/api/attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          course_id: parseInt(selectedCourseId),
          date: attendanceDate,
          records
        })
      });
      const payload = await res.json();
      if (!res.ok) {
        alert(payload?.error || "Error saving attendance");
        return;
      }
      alert("Attendance saved!");
    } catch (err) {
      alert("Error saving attendance");
    }
  };

  const generatePaper = async () => {
    if (!aiCourseId) {
      setError("Select a classroom before generating a question paper.");
      return;
    }
    setGeneratedPaper("");
    setError("");
    setIsGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/question-paper/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: qPaperTopic, difficulty: "Hard", course_id: aiCourseId ? parseInt(aiCourseId) : null })
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
                <h3>Choose Classroom</h3>
                <p>Select the classroom to power the AI tools below.</p>
              </div>
              <div className="card-body">
                <div className="input-row">
                  <select
                    value={aiCourseId}
                    onChange={(e) => setAiCourseId(e.target.value)}
                  >
                    <option value="">Select Classroom</option>
                    {courses.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                {courses.length === 0 && (
                  <div className="placeholder">No courses loaded yet. Sync courses first.</div>
                )}
              </div>
            </div>

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
                    disabled={!aiCourseId}
                  />
                  <button
                    className="primary"
                    onClick={generatePaper}
                    disabled={!aiCourseId || !qPaperTopic || isGenerating}
                  >
                    {isGenerating ? "Generating..." : "Generate"}
                  </button>
                </div>
                {!aiCourseId && (
                  <p className="error">Select a classroom first.</p>
                )}
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
                <p>Analyze turned-in submissions from Google Classroom.</p>
              </div>
              <div className="card-body">
                <div className="input-row">
                  <select
                    value={selectedCourseworkId}
                    onChange={(e) => setSelectedCourseworkId(e.target.value)}
                    disabled={!aiCourseId || courseworkLoading}
                  >
                    <option value="">Select Assignment</option>
                    {courseworkItems.map((item) => (
                      <option key={item.id} value={item.id}>{item.title}</option>
                    ))}
                  </select>
                  <button
                    className="primary"
                    onClick={runPlagiarismCheck}
                    disabled={!aiCourseId || !selectedCourseworkId || plagiarismLoading}
                  >
                    {plagiarismLoading ? "Analyzing..." : "Check Submissions"}
                  </button>
                </div>
                {courseworkLoading && <p>Loading assignments...</p>}
                {plagiarismError && <p className="error">{plagiarismError}</p>}
                {plagiarismResults.length > 0 ? (
                  <table className="attendance-table">
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th style={{ textAlign: 'right' }}>AI %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {plagiarismResults.map((row) => (
                        <tr key={row.student_id}>
                          <td>{row.student_name}</td>
                          <td style={{ textAlign: 'right' }}>
                            {row.percentage === null || row.percentage === undefined ? "N/A" : `${row.percentage}%`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="placeholder">Select a classroom and assignment to run the check.</div>
                )}
              </div>
            </div>
          </section>
        )}
        {activeTab === "timetable" && (
          <section className="stack">
            <Timetablegenerator courses={courses} />
          </section>
        )}
      </div>
    </div>
  );
}











