import React, { useState, useEffect } from 'react';
import './App.css';
import Timetablegenerator from './components/ui/page/Timetablegenerator';
import MeetAttendancePanel from './components/MeetAttendancePanel';
import StudentDashboard from './components/StudentDashboard';
import FeedbackPanel from './components/FeedbackPanel';
function AttendanceReport({ report, loading, onRefresh }) {
  return (
    <div className="card">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3>Attendance Report</h3>
          <p>Overall percentage for all students in this subject.</p>
        </div>
        <button className="ghost" onClick={onRefresh} disabled={loading}>
          {loading ? "Loading..." : "Generate Report"}
        </button>
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

function LandingPage({ onSignIn, isSyncing }) {
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

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [initialFeedbackAssignment, setInitialFeedbackAssignment] = useState("");
  const [initialFeedbackStudent, setInitialFeedbackStudent] = useState("");
  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [students, setStudents] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState({});
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [qPaperTopic, setQPaperTopic] = useState("");
  const [generatedPaper, setGeneratedPaper] = useState("");
  const [docLink, setDocLink] = useState("");
  const [qpOutput, setQpOutput] = useState("google_doc");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [syncError, setSyncError] = useState("");
  const [aiFile, setAiFile] = useState(null);
  const [aiResult, setAiResult] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [user, setUser] = useState(null);
  const [report, setReport] = useState([]);
  const [isReportLoading, setIsReportLoading] = useState(false);
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [customApiKey, setCustomApiKey] = useState("");
  const [isQuotaExceeded, setIsQuotaExceeded] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [targets, setTargets] = useState([]);
  const [targetsLoading, setTargetsLoading] = useState(false);
  const [targetsError, setTargetsError] = useState("");
  const [showTargetForm, setShowTargetForm] = useState(false);
  const [targetTopic, setTargetTopic] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [isSavingTarget, setIsSavingTarget] = useState(false);
  const [complianceMessage, setComplianceMessage] = useState("");
  const [complianceMetrics, setComplianceMetrics] = useState({ coCoverage: 0, poMapping: 0, status: "" });
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [metricsError, setMetricsError] = useState("");
  const [timetableData, setTimetableData] = useState({});
  const [periodTimings, setPeriodTimings] = useState([]);

  const API_BASE = "https://classops-5.onrender.com";

  useEffect(() => {
    fetchUser();
    fetchCourses();
  }, []);

  useEffect(() => {
    if (user) {
      fetchTimetableData();
      if (user.role === 'student' && activeTab === 'overview') {
        setActiveTab('student-dashboard');
      }
    } else {
      setTimetableData({});
      setPeriodTimings([]);
    }
  }, [user]);

  useEffect(() => {
    if (activeTab === "meet" || activeTab === "timetable") {
      fetchTimetableData();
    }
  }, [activeTab]);

  useEffect(() => {
    if (selectedCourseId) {
      fetchAssignments(selectedCourseId);
    }
  }, [selectedCourseId]);

  const updateServerKey = async () => {
    if (!customApiKey.trim()) {
      alert("Please enter a key first.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/config/update-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: customApiKey.trim() })
      });
      const data = await res.json();
      if (res.ok) {
        alert("Server API Key updated successfully!");
        setIsQuotaExceeded(false); // Hide the box as it's now updated
      } else {
        alert(data.error || "Failed to update key.");
      }
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const fetchAssignments = async (courseId) => {
    try {
      const res = await fetch(`${API_BASE}/api/courses/${courseId}/assignments`, { credentials: "include" });
      const data = await res.json();
      setAssignments(Array.isArray(data) ? data : []);
      if (Array.isArray(data) && data.length > 0) {
        setSelectedAssignmentId(data[0].id.toString());
      } else {
        setSelectedAssignmentId("");
      }
    } catch (err) {
      console.error("Failed to fetch assignments", err);
    }
  };

  const syncAssignments = async () => {
    if (!selectedCourseId) {
      alert("Please select a subject first.");
      return;
    }
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/courses/${selectedCourseId}/sync-assignments`, {
        method: "POST",
        credentials: "include"
      });
      const data = await res.json();
      if (res.ok) {
        fetchAssignments(selectedCourseId);
        alert(data.message || "Assignments synced successfully!");
      } else {
        alert(data.error || "Sync failed.");
      }
    } catch (err) {
      console.error("Sync assignments error:", err);
      alert("Error syncing assignments.");
    } finally {
      setIsSyncing(false);
    }
  };

  const analyzeSubmissions = async () => {
    if (!selectedAssignmentId) {
      alert("Please select an assignment first.");
      return;
    }
    setIsAnalyzing(true);
    setAnalysisData(null);
    setAiError("");
    try {
      const res = await fetch(`${API_BASE}/api/courses/${selectedCourseId}/assignments/${selectedAssignmentId}/analyze`, {
        method: "POST",
        credentials: "include"
      });
      const data = await res.json();
      if (res.ok) {
        setAnalysisData(data);
      } else {
        setAiError(data.error || "Analysis failed.");
      }
    } catch (err) {
      console.error("Analysis error:", err);
      setAiError("Error during submission analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const fetchReport = async () => {
    if (!selectedCourseId) return;
    setIsReportLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/attendance/report/${selectedCourseId}`, { credentials: "include" });
      const data = await res.json();
      setReport(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch report", err);
    } finally {
      setIsReportLoading(false);
    }
  };

  const formatTargetDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(`${dateStr}T00:00:00`);
    if (Number.isNaN(date.getTime())) return dateStr;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const fetchTargets = async (courseId) => {
    setTargetsError("");
    if (!courseId) {
      setTargets([]);
      return;
    }
    setTargetsLoading(true);
    setTargetsError("");
    try {
      const res = await fetch(`${API_BASE}/api/targets?course_id=${courseId}`, { credentials: "include" });
      const data = await res.json();
      if (res.ok) {
        setTargets(Array.isArray(data) ? data : []);
      } else {
        setTargets([]);
        setTargetsError(data?.error || "Failed to load targets.");
      }
    } catch (err) {
      console.error("Failed to fetch targets", err);
      setTargetsError("Failed to load targets.");
      setTargets([]);
    } finally {
      setTargetsLoading(false);
    }
  };
  const fetchComplianceMetrics = async (courseId) => {
    setMetricsError("");
    setMetricsLoading(true);
    try {
      const query = courseId ? `?course_id=${courseId}` : "";
      const res = await fetch(`${API_BASE}/api/metrics/compliance${query}`, { credentials: "include" });
      const data = await res.json();
      if (res.ok) {
        setComplianceMetrics({
          coCoverage: data.co_coverage ?? 0,
          poMapping: data.po_mapping ?? 0,
          status: data.status || ""
        });
      } else {
        setMetricsError(data?.error || "Failed to load compliance metrics.");
      }
    } catch (err) {
      console.error("Failed to fetch compliance metrics", err);
      setMetricsError("Failed to load compliance metrics.");
    } finally {
      setMetricsLoading(false);
    }
  };
  const handleAddTarget = async () => {
    if (!selectedCourseId) {
      alert("Please select a subject first.");
      return;
    }
    if (!targetTopic || !targetDate) {
      alert("Please enter a topic and due date.");
      return;
    }
    setIsSavingTarget(true);
    try {
      const res = await fetch(`${API_BASE}/api/targets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          topic: targetTopic.trim(),
          date: targetDate,
          course_id: parseInt(selectedCourseId)
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Failed to add target.");
      }
      setTargetTopic("");
      setTargetDate("");
      setShowTargetForm(false);
      fetchTargets(selectedCourseId);
    } catch (err) {
      console.error("Add target error:", err);
      alert(err?.message || "Could not add target.");
    } finally {
      setIsSavingTarget(false);
    }
  };

  const toggleTargetStatus = async (targetId, completed) => {
    setIsSavingTarget(true);
    try {
      const res = await fetch(`${API_BASE}/api/courses/${selectedCourseId}/targets/${targetId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ completed })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Failed to update target.");
      }
      setTargets((prev) => prev.map((t) => (t.id === targetId ? { ...t, completed: data.completed } : t)));
    } catch (err) {
      console.error("Update target error:", err);
      alert(err?.message || "Could not update target.");
    } finally {
      setIsSavingTarget(false);
    }
  };

  const downloadBlob = (blob, filename) => {
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const generateComplianceReport = async () => {
    setComplianceMessage("");
    try {
      const query = selectedCourseId ? `?course_id=${selectedCourseId}` : "";
      const res = await fetch(`${API_BASE}/api/reports/compliance.pdf${query}`, {
        credentials: "include"
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error || "Failed to generate report.");
      }
      const blob = await res.blob();
      const course = courses.find((c) => c.id.toString() === selectedCourseId);
      const today = new Date().toISOString().split("T")[0];
      const safeCourse = (course?.name || "all_courses").replace(/[^a-z0-9]+/gi, "_").toLowerCase();
      const filename = `nba_compliance_report_${safeCourse}_${today}.pdf`;
      downloadBlob(blob, filename);
      setComplianceMessage("Compliance report downloaded.");
      setTimeout(() => setComplianceMessage(""), 3000);
    } catch (err) {
      console.error("Compliance report error:", err);
      setComplianceMessage(err?.message || "Failed to generate report.");
    }
  };

  const fetchUser = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/me`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated) {
          setUser(data.user);
        }
      }
    } catch (err) {
      console.error("Failed to fetch user session", err);
    } finally {
      setAuthChecked(true);
    }
  };

  const handleLogout = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/logout`, { 
        method: "POST",
        credentials: "include" 
      });
      if (res.ok) {
        setUser(null);
        setCourses([]);
        alert("Logged out successfully");
      }
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const fetchCourses = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/courses`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setCourses(Array.isArray(data) ? data : []);
        if (Array.isArray(data) && data.length > 0 && !selectedCourseId) {
          const firstActiveCourse = data.find((course) => Number(course?.hours_per_week || 0) > 0);
          setSelectedCourseId((firstActiveCourse || data[0]).id.toString());
        }
      } else if (res.status === 401) {
        setCourses([]);
        setUser(null);
      }
    } catch (err) {
      console.error("Failed to fetch courses", err);
    }
  };

  const fetchTimetableData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/timetable`, { credentials: "include" });
      const data = await res.json();
      if (res.ok && data?.timetable) {
        setTimetableData(data.timetable);
        setPeriodTimings(Array.isArray(data?.period_timings) ? data.period_timings : []);
      } else {
        setTimetableData({});
        setPeriodTimings([]);
      }
    } catch (err) {
      console.error("Failed to fetch timetable", err);
      setTimetableData({});
      setPeriodTimings([]);
    }
  };

  const fetchStudents = async (courseId) => {
    if (!courseId) return;
    try {
      const res = await fetch(`${API_BASE}/api/courses/${courseId}/students`, { credentials: "include" });
      const data = await res.json();
      setStudents(Array.isArray(data) ? data : []);

      const initial = {};
      (Array.isArray(data) ? data : []).forEach(s => initial[s.id] = "Present");
      setAttendanceRecords(initial);
    } catch (err) {
      console.error("Failed to fetch students", err);
    }
  };

  const handleMeetAttendanceMapped = (rows) => {
    if (!Array.isArray(rows) || rows.length === 0) {
      return;
    }

    const presentEmails = new Set(
      rows
        .map((row) => row?.email?.toLowerCase())
        .filter(Boolean)
    );

    setAttendanceRecords((prev) => {
      const next = { ...prev };
      students.forEach((student) => {
        if (student.email && presentEmails.has(student.email.toLowerCase())) {
          next[student.id] = "Present";
        }
      });
      return next;
    });
  };

  const syncStudents = async () => {
    if (!selectedCourseId) {
      alert("Please select a subject first.");
      return;
    }
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/courses/${selectedCourseId}/sync-students`, {
        method: "POST",
        credentials: "include"
      });
      const data = await res.json();
      if (res.ok) {
        fetchStudents(selectedCourseId);
        alert(data.message || "Students synced successfully!");
      } else {
        alert(data.error || "Sync failed. Please ensure you are signed in and have classroom permissions.");
      }
    } catch (err) {
      console.error("Sync students error:", err);
      alert("Error syncing students. Check your internet connection or backend server.");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSignIn = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/google/url`, { credentials: "include" });
      const data = await res.json();
      if (data.auth_url) {
        window.location.href = data.auth_url;
      } else {
        alert("Could not get authentication URL.");
      }
    } catch (err) {
      console.error("Auth URL fetch failed", err);
      // Fallback to direct redirect if API fails
      window.location.href = `${API_BASE}/api/auth/google`;
    }
  };

  const handleSyncCourses = async () => {
    setSyncError("");
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/classroom/sync`, { credentials: "include" });
      if (res.status === 401) {
        handleSignIn();
        return;
      }
      const data = await res.json();
      if (res.ok) {
        await fetchCourses();
        alert("Courses synced successfully!");
      } else {
        setSyncError(data.error || "Sync failed");
      }
    } catch (err) {
      console.error("Sync courses error:", err);
      setSyncError("Could not sync courses. Check connection or backend.");
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    if (selectedCourseId) {
      fetchStudents(selectedCourseId);
    }
  }, [selectedCourseId]);

  useEffect(() => {
    if (selectedCourseId) {
      fetchReport();
    }
  }, [selectedCourseId]);
  useEffect(() => {
    if (!user) {
      setTargets([]);
      setComplianceMetrics({ coCoverage: 0, poMapping: 0, status: "" });
      return;
    }
    if (selectedCourseId) {
      fetchTargets(selectedCourseId);
      fetchComplianceMetrics(selectedCourseId);
    } else {
      fetchComplianceMetrics("");
    }
  }, [selectedCourseId, user]);

  useEffect(() => {
    if (selectedCourseId && attendanceDate) {
      fetchAttendance();
    }
  }, [selectedCourseId, attendanceDate]);

  const fetchAttendance = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/attendance?course_id=${selectedCourseId}&date=${attendanceDate}`, { 
        credentials: "include" 
      });
      const data = await res.json();
      if (res.ok && data.records) {
        // Merge with existing students to ensure everyone is listed
        setAttendanceRecords(prev => {
          const updated = { ...prev };
          Object.entries(data.records).forEach(([sId, status]) => {
            updated[sId] = status;
          });
          return updated;
        });
      }
    } catch (err) {
      console.error("Failed to fetch attendance records", err);
    }
  };

  const handleAttendanceChange = (studentId, status) => {
    setAttendanceRecords(prev => ({ ...prev, [studentId]: status }));
  };

  const saveAttendance = async () => {
    try {
      const records = Object.entries(attendanceRecords).map(([id, status]) => ({
        student_id: parseInt(id),
        status
      }));

      await fetch("https://classops-5.onrender.com/api/attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_id: parseInt(selectedCourseId),
          date: attendanceDate,
          records
        }),
        credentials: "include"
      });
      alert("Attendance saved!");
      fetchReport();
    } catch (err) {
      alert("Error saving attendance");
    }
  };

  const generatePaper = async () => {
    setGeneratedPaper("");
    setDocLink("");
    setError("");
    setIsGenerating(true);
    
    // Find the course name for the selected ID
    const selectedCourse = courses.find(c => c.id.toString() === selectedCourseId);
    const courseName = selectedCourse ? selectedCourse.name : "General Course";

    try {
      const payload = { topic: qPaperTopic, difficulty: "Medium", course_name: courseName, output: qpOutput };
      const trimmedKey = customApiKey.trim();
      if (trimmedKey) {
        payload.api_key = trimmedKey;
      }
      const res = await fetch(`${API_BASE}/api/question-paper/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
      });

      if (qpOutput === "docx") {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          const errText = (data?.error || "").toLowerCase();
          if (res.status === 429 || errText.includes("quota") || errText.includes("api key") || errText.includes("invalid")) {
            setIsQuotaExceeded(true);
          }
          throw new Error(data?.error || `Request failed with status ${res.status}`);
        }
        const blob = await res.blob();
        const safeCourse = (courseName || "question_paper").replace(/[^a-z0-9]+/gi, "_").toLowerCase();
        const today = new Date().toISOString().split("T")[0];
        downloadBlob(blob, `question_paper_${safeCourse}_${today}.docx`);
        setIsQuotaExceeded(false);
        setError("");
        return;
      }

      const data = await res.json();
      if (!res.ok) {
        const errText = (data?.error || "").toLowerCase();
        if (res.status === 429 || errText.includes("quota") || errText.includes("api key") || errText.includes("invalid")) {
          setIsQuotaExceeded(true);
        }
        if (res.status === 401 && qpOutput === "google_doc") {
          throw new Error("Please sign in again to grant Google Drive access.");
        }
        throw new Error(data?.error || `Request failed with status ${res.status}`);
      }

      if (qpOutput === "google_doc") {
        if (!data?.doc_url) {
          throw new Error("No Google Doc link returned. Make sure you are signed in and Drive access is granted.");
        }
        setDocLink(data.doc_url);
      } else {
        const content = data?.question_paper || data?.questionPaper || "No question paper returned.";
        setGeneratedPaper(content);
      }
      setError("");
      setIsQuotaExceeded(false);
    } catch (err) {
      setError(err?.message || "Could not generate the question paper.");
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

  if (!authChecked) {
    return (
      <div className="app">
        <div className="placeholder">Checking your session...</div>
      </div>
    );
  }

  if (!user) {
    return <LandingPage onSignIn={handleSignIn} isSyncing={isSyncing} />;
  }

  // Define tabs robustly: default to Teacher tabs unless explicitly a 'student'
  const isStudent = user?.role === 'student';
  const activeTabs = isStudent 
    ? [{ id: "student-dashboard", label: "Student Dashboard" }]
    : [
        { id: "overview", label: "Overview & Targets" },
        { id: "attendance", label: "Attendance" },
        { id: "meet", label: "Meet" },
        { id: "ai-tools", label: "AI Tools" },
        { id: "feedback", label: "Feedback & Grading" },
        { id: "timetable", label: "Timetable" }
      ];

  // Debug hook to track user state in production
  useEffect(() => {
    console.log("=== RENDER DEBUG ===");
    console.log("Current User Object:", user);
    console.log("Evaluated Role:", user?.role);
    console.log("Final Tabs Array:", activeTabs);
  }, [user]);

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="kicker">Teacher Workflow Automation</p>
          <h1>ClassOps</h1>
          <p className="subtitle">Keep syllabus targets, compliance metrics, and AI tools in one focused workspace.</p>
        </div>
        <div className="auth-section">
          {user ? (
            <div className="user-profile">
              {user.picture && <img src={user.picture} alt={user.name} className="avatar" />}
              <div className="user-info">
                <span className="user-name">{user.name}</span>
                <button className="ghost sm" onClick={handleLogout}>Logout</button>
              </div>
            </div>
          ) : (
            <button className="primary" onClick={handleSignIn} disabled={isSyncing}>
              {isSyncing ? "Connecting..." : "Sign in with Google"}
            </button>
          )}
        </div>
      </header>

      <div className="tabs">
        <div className="tab-list">
          {activeTabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "feedback" && (
          <FeedbackPanel
            apiBase={API_BASE}
            courses={courses}
            courseId={selectedCourseId}
            onCourseChange={setSelectedCourseId}
            isSyncing={isSyncing}
            initialAssignmentId={initialFeedbackAssignment}
            initialUserId={initialFeedbackStudent}
            readOnly={user?.role === 'student'}
          />
        )}

        {activeTab === "overview" && (
          <section className="grid">
            <div className="card">
              <div className="card-header">
                <h3>Material & Target Completion</h3>
                <p>Track progress by unit and upcoming deadlines.</p>
              </div>
              <div className="card-body">
                <div className="input-row">
                  <select
                    value={selectedCourseId}
                    onChange={(e) => setSelectedCourseId(e.target.value)}
                  >
                    <option value="">Select Subject</option>
                    {courses.map((course) => (
                      <option key={course.id} value={course.id}>{course.name}</option>
                    ))}
                  </select>
                  <button
                    className="ghost"
                    onClick={() => setShowTargetForm((prev) => !prev)}
                    disabled={!selectedCourseId}
                  >
                    {showTargetForm ? "Close" : "+ Add Syllabus Target"}
                  </button>
                </div>

                {showTargetForm && (
                  <div className="target-form">
                    <input
                      placeholder="Enter unit or topic (e.g., Unit 3: Databases)"
                      value={targetTopic}
                      onChange={(e) => setTargetTopic(e.target.value)}
                    />
                    <input
                      type="date"
                      value={targetDate}
                      onChange={(e) => setTargetDate(e.target.value)}
                    />
                    <button className="primary" onClick={handleAddTarget} disabled={isSavingTarget}>
                      {isSavingTarget ? "Adding..." : "Add Target"}
                    </button>
                    <button className="ghost" onClick={() => setShowTargetForm(false)} disabled={isSavingTarget}>
                      Cancel
                    </button>
                  </div>
                )}

                {targetsLoading ? (
                  <p>Loading syllabus targets...</p>
                ) : targets.length > 0 ? (
                  <ul className="list">
                    {targets.map((target) => (
                      <li key={target.id}>
                        <div className="target-info">
                          <span>{target.topic}</span>
                          {target.course_name && <span className="target-course">{target.course_name}</span>}
                        </div>
                        <div className="target-actions">
                          <button
                            className={`status-pill ${target.completed ? "completed" : "pending"}`}
                            onClick={() => toggleTargetStatus(target.id, !target.completed)}
                            disabled={isSavingTarget}
                          >
                            {target.completed
                              ? "Completed"
                              : `Pending${target.date ? ` (Due: ${formatTargetDate(target.date)})` : ""}`}
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="placeholder">
                    {selectedCourseId ? "No targets added yet. Add a syllabus target to get started." : "Select a subject to view syllabus targets."}
                  </div>
                )}

                {targetsError && <p className="hint" style={{ color: "#c53030" }}>{targetsError}</p>}
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
                    <p className="metric-value">{complianceMetrics.coCoverage}%</p>
                  </div>
                  <div>
                    <p className="metric-label">PO Mapping</p>
                    <p className="metric-value">{complianceMetrics.poMapping}%</p>
                  </div>
                </div>
                {metricsLoading && <p className="hint">Analyzing metrics...</p>}
                {metricsError && <p className="hint" style={{ color: "#c53030" }}>{metricsError}</p>}
                {complianceMetrics.status && <p className="hint">Status: {complianceMetrics.status}</p>}
                <p className="hint">Based on completed syllabus targets and attendance records.</p>
                <button className="primary full" onClick={generateComplianceReport}>
                  Generate NBA Compliance Report
                </button>
                {complianceMessage && <p className="hint">{complianceMessage}</p>}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3>Google Classroom Courses</h3>
                <p>Synced courses from your connected Google Classroom account.</p>
              </div>
              <div className="card-body">
                <button className="primary" onClick={handleSyncCourses} disabled={isSyncing}>
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
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3>Subject-wise Attendance</h3>
                  <p>Log presence for the selected subject and date.</p>
                </div>
                <button className="ghost" onClick={() => setActiveTab('feedback')} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
                  View Feedback
                </button>
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
                        <th>Actions</th>
                        <th style={{ textAlign: 'right' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.map((s) => (
                        <tr key={s.id}>
                          <td>{s.roll_number}</td>
                          <td>{s.name}</td>
                          <td>
                            <button 
                              className="ghost" 
                              onClick={() => {
                                setInitialFeedbackStudent(s.google_student_id || s.id);
                                setActiveTab("feedback");
                              }}
                              style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                            >
                              Grade/Feedback
                            </button>
                          </td>
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

            <AttendanceReport 
              report={report} 
              loading={isReportLoading} 
              onRefresh={fetchReport} 
            />
          </section>
        )}

        {activeTab === "meet" && (
          <MeetAttendancePanel
            apiBase={API_BASE}
            courses={courses}
            courseId={selectedCourseId}
            onCourseChange={setSelectedCourseId}
            students={students}
            timetableData={timetableData}
            periodTimings={periodTimings}
            onAttendanceMapped={handleMeetAttendanceMapped}
            onSyncStudents={syncStudents}
            isSyncing={isSyncing}
          />
        )}

        {activeTab === "ai-tools" && (
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
        )}

        {activeTab === "timetable" && (
          <section className="stack">
            <Timetablegenerator courses={courses} />
          </section>
        )}

        {activeTab === "student-dashboard" && (
          <StudentDashboard 
            API_BASE={API_BASE} 
            onReadFeedback={(courseId, assignmentId) => {
              if (courseId) setSelectedCourseId(courseId);
              setInitialFeedbackAssignment(assignmentId);
              setInitialFeedbackStudent(user?.google_student_id || user?.id);
              setActiveTab("feedback");
            }}
          />
        )}
      </div>
    </div>
  );
}




















