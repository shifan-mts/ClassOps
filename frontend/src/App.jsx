import React, { useState, useEffect } from 'react';
import './App.css';
import { usePermissions } from './context/PermissionContext';

import Header from './components/Header';
import LandingPage from './components/LandingPage';
import DashboardPanel from './components/DashboardPanel';
import AttendancePanel from './components/AttendancePanel';
import AIToolsPanel from './components/AIToolsPanel';
import EvaluationPanel from './components/EvaluationPanel';
import MeetAttendancePanel from './components/MeetAttendancePanel';
import StudentDashboard from './components/StudentDashboard';
import Timetablegenerator from './components/ui/page/Timetablegenerator';

export default function App() {
  const { hasPermission, loading: permsLoading, refreshPermissions } = usePermissions();
  
  // --- State ---
  const [activeTab, setActiveTab] = useState("");
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [students, setStudents] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState({});
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState("");
  
  // Stats for the unified Dashboard
  const [stats, setStats] = useState(null);

  // AI Tools State
  const [qPaperTopic, setQPaperTopic] = useState("");
  const [generatedPaper, setGeneratedPaper] = useState("");
  const [docLink, setDocLink] = useState("");
  const [qpOutput, setQpOutput] = useState("google_doc");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [customApiKey, setCustomApiKey] = useState("");
  const [isQuotaExceeded, setIsQuotaExceeded] = useState(false);
  
  // Submission Analysis State
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [aiError, setAiError] = useState("");
  
  // Manual AI Check State
  const [aiFile, setAiFile] = useState(null);
  const [aiResult, setAiResult] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  
  // Attendance Report State
  const [report, setReport] = useState([]);
  const [isReportLoading, setIsReportLoading] = useState(false);
  
  // Syllabus Targets & Compliance State
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
  
  // Timetable State
  const [timetableData, setTimetableData] = useState({});
  const [periodTimings, setPeriodTimings] = useState([]);
  
  // Feedback Selection State
  const [initialFeedbackStudent, setInitialFeedbackStudent] = useState("");
  const [initialFeedbackAssignment, setInitialFeedbackAssignment] = useState("");

  const API_BASE = import.meta.env.DEV ? "http://localhost:5000" : window.location.origin;

  // --- Initial Data Loading ---
  useEffect(() => {
    fetchUser();
    fetchCourses();
  }, []);

  useEffect(() => {
    if (user) {
      fetchTimetableData();
      fetchDashboardStats();
      refreshPermissions();
      
      const allPossibleTabIds = [
        "teacher-dashboard", "student-dashboard", "attendance", "meet", "ai-tools", "evaluation", "timetable"
      ];
      
      const accessibleTabs = allPossibleTabIds.filter(id => hasPermission(id, "view") || hasPermission(id, "edit") || hasPermission(id, "access"));

      if (accessibleTabs.length > 0 && (!activeTab || !accessibleTabs.includes(activeTab))) {
        setActiveTab(accessibleTabs[0]);
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
    if (activeTab === "teacher-dashboard") {
      fetchDashboardStats();
    }
  }, [activeTab]);

  useEffect(() => {
    if (selectedCourseId) {
      fetchAssignments(selectedCourseId);
      fetchStudents(selectedCourseId);
      fetchReport(selectedCourseId);
      fetchTargets(selectedCourseId);
      fetchComplianceMetrics(selectedCourseId);
    }
  }, [selectedCourseId]);

  useEffect(() => {
    if (selectedCourseId && attendanceDate) {
      fetchAttendance();
    }
  }, [selectedCourseId, attendanceDate]);

  // --- API Functions ---

  const fetchUser = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/me`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated) setUser(data.user);
        else setUser(null);
      } else setUser(null);
    } catch (err) {
      console.error("Failed to fetch user session", err);
      setUser(null);
    } finally {
      setAuthChecked(true);
    }
  };

  const fetchCourses = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/courses`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        const coursesList = Array.isArray(data) ? data : [];
        setCourses(coursesList);
        if (coursesList.length > 0 && !selectedCourseId) {
          const firstActive = coursesList.find(c => Number(c?.hours_per_week || 0) > 0);
          setSelectedCourseId((firstActive || coursesList[0]).id.toString());
        }
      } else if (res.status === 401) setUser(null);
    } catch (err) {
      console.error("Failed to fetch courses", err);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard/stats`, { credentials: "include" });
      if (res.ok) setStats(await res.json());
    } catch (err) {
      console.error("Failed to fetch stats", err);
    }
  };

  const fetchTimetableData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/timetable`, { credentials: "include" });
      const data = await res.json();
      if (res.ok && data?.timetable) {
        setTimetableData(data.timetable);
        setPeriodTimings(Array.isArray(data?.period_timings) ? data.period_timings : []);
      }
    } catch (err) {
      console.error("Failed to fetch timetable", err);
    }
  };

  const handleSignIn = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/google/url`, { credentials: "include" });
      const data = await res.json();
      if (data.auth_url) window.location.href = data.auth_url;
      else window.location.href = `${API_BASE}/api/auth/google`;
    } catch (err) {
      window.location.href = `${API_BASE}/api/auth/google`;
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, { method: "POST", credentials: "include" });
      setUser(null);
      setCourses([]);
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const handleSyncCourses = async () => {
    setSyncError("");
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/classroom/sync`, { credentials: "include" });
      if (res.status === 401) return handleSignIn();
      if (res.ok) {
        await fetchCourses();
        alert("Courses synced successfully!");
      } else {
        const data = await res.json();
        setSyncError(data.error || "Sync failed");
      }
    } catch (err) {
      setSyncError("Could not sync courses.");
    } finally {
      setIsSyncing(false);
    }
  };

  const fetchTargets = async (courseId) => {
    setTargetsError("");
    setTargetsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/targets?course_id=${courseId}`, { credentials: "include" });
      const data = await res.json();
      if (res.ok) setTargets(Array.isArray(data) ? data : []);
      else setTargetsError(data?.error || "Failed to load targets.");
    } catch (err) {
      setTargetsError("Failed to load targets.");
    } finally {
      setTargetsLoading(false);
    }
  };

  const handleAddTarget = async () => {
    if (!selectedCourseId || !targetTopic || !targetDate) {
      alert("Please complete the form.");
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
      if (res.ok) {
        setTargetTopic("");
        setTargetDate("");
        setShowTargetForm(false);
        fetchTargets(selectedCourseId);
      } else {
        const data = await res.json();
        alert(data?.error || "Failed to add target.");
      }
    } catch (err) {
      alert("Error adding target.");
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
      if (res.ok) {
        const data = await res.json();
        setTargets(prev => prev.map(t => t.id === targetId ? { ...t, completed: data.completed } : t));
      }
    } catch (err) {
      alert("Update failed.");
    } finally {
      setIsSavingTarget(false);
    }
  };

  const fetchComplianceMetrics = async (courseId) => {
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
      }
    } catch (err) {
      console.error("Compliance fetch failed", err);
    } finally {
      setMetricsLoading(false);
    }
  };

  const generateComplianceReport = async () => {
    setComplianceMessage("Generating...");
    try {
      const query = selectedCourseId ? `?course_id=${selectedCourseId}` : "";
      const res = await fetch(`${API_BASE}/api/reports/compliance.pdf${query}`, { credentials: "include" });
      if (!res.ok) throw new Error("Failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `compliance_report_${selectedCourseId || 'all'}.pdf`;
      a.click();
      setComplianceMessage("Downloaded.");
    } catch (err) {
      setComplianceMessage("Generation failed.");
    }
  };

  const fetchStudents = async (courseId) => {
    try {
      const res = await fetch(`${API_BASE}/api/courses/${courseId}/students`, { credentials: "include" });
      const data = await res.json();
      const studentsList = Array.isArray(data) ? data : [];
      setStudents(studentsList);
      const initial = {};
      studentsList.forEach(s => initial[s.id] = "Present");
      setAttendanceRecords(initial);
    } catch (err) {
      console.error("Students fetch failed", err);
    }
  };

  const syncStudents = async () => {
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/courses/${selectedCourseId}/sync-students`, {
        method: "POST",
        credentials: "include"
      });
      if (res.ok) {
        fetchStudents(selectedCourseId);
        alert("Students synced.");
      }
    } catch (err) {
      alert("Sync failed.");
    } finally {
      setIsSyncing(false);
    }
  };

  const fetchAttendance = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/attendance?course_id=${selectedCourseId}&date=${attendanceDate}`, { 
        credentials: "include" 
      });
      const data = await res.json();
      if (res.ok && data.records) setAttendanceRecords(prev => ({ ...prev, ...data.records }));
    } catch (err) {
      console.error("Attendance fetch failed", err);
    }
  };

  const saveAttendance = async () => {
    if (!selectedCourseId) {
      alert("Please select a subject first.");
      return;
    }
    try {
      const records = Object.entries(attendanceRecords).map(([id, status]) => ({
        student_id: id,
        status
      }));
      const res = await fetch(`${API_BASE}/api/attendance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_id: selectedCourseId,
          date: attendanceDate,
          records
        }),
        credentials: "include"
      });
      if (res.ok) {
        alert("Attendance saved successfully!");
        fetchReport(selectedCourseId);
      } else {
        const data = await res.json();
        alert(data.error || "Failed to save attendance.");
      }
    } catch (err) {
      console.error("Save attendance error:", err);
      alert("Error saving attendance");
    }
  };

  const handleMarkAllPresent = () => {
    setAttendanceRecords(prev => {
      const next = { ...prev };
      students.forEach(s => { next[s.id] = "Present"; });
      return next;
    });
  };

  const handleExportCSV = () => {
    if (students.length === 0) return alert("No data to export.");
    const headers = ["Roll Number", "Name", "Status"];
    const rows = students.map(s => [s.roll_number, s.name, attendanceRecords[s.id] || "Present"]);
    let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n" + rows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `attendance_${selectedCourseId}_${attendanceDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const fetchReport = async (courseId) => {
    if (!courseId) return;
    setIsReportLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/attendance/report/${courseId}`, { credentials: "include" });
      const data = await res.json();
      setReport(Array.isArray(data) ? data : []);
    } finally {
      setIsReportLoading(false);
    }
  };

  const fetchAssignments = async (courseId) => {
    try {
      const res = await fetch(`${API_BASE}/api/courses/${courseId}/assignments`, { credentials: "include" });
      const data = await res.json();
      const list = Array.isArray(data) ? data : [];
      setAssignments(list);
      if (list.length > 0) setSelectedAssignmentId(list[0].id.toString());
    } catch (err) {
      console.error("Assignments fetch failed", err);
    }
  };

  const generatePaper = async () => {
    setIsGenerating(true);
    setError("");
    setGeneratedPaper("");
    setDocLink("");
    try {
      const course = courses.find(c => c.id.toString() === selectedCourseId);
      const payload = { 
        topic: qPaperTopic, 
        difficulty: "Medium", 
        course_name: course?.name || "General",
        output: qpOutput
      };
      if (customApiKey.trim()) payload.api_key = customApiKey.trim();

      const res = await fetch(`${API_BASE}/api/question-paper/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
      });

      if (qpOutput === "docx") {
        if (!res.ok) throw new Error("Generation failed.");
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `qpaper_${qPaperTopic.replace(/\s+/g, '_')}.docx`;
        a.click();
        return;
      }

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) setIsQuotaExceeded(true);
        throw new Error(data.error || "Failed");
      }
      if (qpOutput === "google_doc") setDocLink(data.doc_url);
      else setGeneratedPaper(data.question_paper || "No content.");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAiCheck = async () => {
    if (!aiFile) return;
    setAiLoading(true);
    try {
      const fd = new FormData();
      fd.append("file", aiFile);
      const res = await fetch(`${API_BASE}/api/assignments/check`, {
        method: "POST",
        body: fd,
        credentials: "include"
      });
      const data = await res.json();
      setAiResult(typeof data.formatted === "string" ? data.formatted : JSON.stringify(data.formatted, null, 2));
    } finally {
      setAiLoading(false);
    }
  };

  if (!authChecked) return <div className="app"><div className="placeholder">Loading ClassOps...</div></div>;
  if (!user) return <LandingPage onSignIn={handleSignIn} isSyncing={isSyncing} />;

  // Dynamic Tab Calculation
  const allPossibleTabs = [
    { id: "teacher-dashboard", label: "Insights" },
    { id: "student-dashboard", label: "Portal" },
    { id: "attendance", label: "Attendance" },
    { id: "meet", label: "Meet" },
    { id: "ai-tools", label: "AI Tools" },
    { id: "evaluation", label: "Evaluations" },
    { id: "timetable", label: "Timetable" }
  ];

  const tabs = allPossibleTabs.filter(tab => hasPermission(tab.id, "view") || hasPermission(tab.id, "edit"));

  return (
    <div className="app">
      <Header user={user} handleLogout={handleLogout} handleSignIn={handleSignIn} isSyncing={isSyncing} />

      <div className="tabs">
        <div className="tab-list">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Dynamic Panel Rendering */}
        
        {activeTab === "student-dashboard" && (hasPermission("student-dashboard", "view") || hasPermission("student-dashboard", "edit")) && (
          <StudentDashboard 
            API_BASE={API_BASE} 
            user={user}
            onReadFeedback={(c, a) => {
              setSelectedCourseId(c);
              setInitialFeedbackAssignment(a);
              setInitialFeedbackStudent(user?.google_student_id || user?.id);
              setActiveTab("evaluation");
            }}
          />
        )}

        {activeTab === "teacher-dashboard" && (hasPermission("teacher-dashboard", "view") || hasPermission("teacher-dashboard", "edit")) && (
          <DashboardPanel 
            user={user}
            stats={stats}
            selectedCourseId={selectedCourseId}
            setSelectedCourseId={setSelectedCourseId}
            courses={courses}
            showTargetForm={showTargetForm}
            setShowTargetForm={setShowTargetForm}
            targetTopic={targetTopic}
            setTargetTopic={setTargetTopic}
            targetDate={targetDate}
            setTargetDate={setTargetDate}
            handleAddTarget={handleAddTarget}
            isSavingTarget={isSavingTarget}
            targets={targets}
            targetsLoading={targetsLoading}
            toggleTargetStatus={toggleTargetStatus}
            complianceMetrics={complianceMetrics}
            generateComplianceReport={generateComplianceReport}
            handleSyncCourses={handleSyncCourses}
            isSyncing={isSyncing}
          />
        )}

        {activeTab === "attendance" && (hasPermission("attendance", "view") || hasPermission("attendance", "edit")) && (
          <AttendancePanel 
            selectedCourseId={selectedCourseId}
            setSelectedCourseId={setSelectedCourseId}
            courses={courses}
            attendanceDate={attendanceDate}
            setAttendanceDate={setAttendanceDate}
            syncStudents={syncStudents}
            isSyncing={isSyncing}
            saveAttendance={saveAttendance}
            students={students}
            attendanceRecords={attendanceRecords}
            handleAttendanceChange={(id, stat) => setAttendanceRecords(p => ({ ...p, [id]: stat }))}
            handleMarkAllPresent={handleMarkAllPresent}
            handleExportCSV={handleExportCSV}
            report={report}
            isReportLoading={isReportLoading}
            fetchReport={() => fetchReport(selectedCourseId)}
            onViewFeedback={(studentId) => {
              if (studentId) setInitialFeedbackStudent(studentId);
              setActiveTab("evaluation");
            }}
          />
        )}

        {activeTab === "meet" && (hasPermission("meet", "view") || hasPermission("meet", "edit")) && (
          <MeetAttendancePanel
            apiBase={API_BASE}
            courses={courses}
            courseId={selectedCourseId}
            onCourseChange={setSelectedCourseId}
            students={students}
            timetableData={timetableData}
            periodTimings={periodTimings}
            onAttendanceMapped={(rows) => {
              const present = new Set(rows.map(r => r?.email?.toLowerCase()).filter(Boolean));
              setAttendanceRecords(prev => {
                const next = { ...prev };
                students.forEach(s => { if (s.email && present.has(s.email.toLowerCase())) next[s.id] = "Present"; });
                return next;
              });
            }}
            onSyncStudents={syncStudents}
            isSyncing={isSyncing}
          />
        )}

        {activeTab === "ai-tools" && (hasPermission("ai-tools", "view") || hasPermission("ai-tools", "edit")) && (
          <AIToolsPanel 
            isQuotaExceeded={isQuotaExceeded}
            customApiKey={customApiKey}
            setCustomApiKey={setCustomApiKey}
            updateServerKey={async () => {
              await fetch(`${API_BASE}/api/config/update-key`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: customApiKey.trim() })
              });
              setIsQuotaExceeded(false);
            }}
            selectedCourseId={selectedCourseId}
            setSelectedCourseId={setSelectedCourseId}
            courses={courses}
            qPaperTopic={qPaperTopic}
            setQPaperTopic={setQPaperTopic}
            qpOutput={qpOutput}
            setQpOutput={setQpOutput}
            generatePaper={generatePaper}
            isGenerating={isGenerating}
            error={error}
            docLink={docLink}
            generatedPaper={generatedPaper}
            syncAssignments={async () => {
              setIsSyncing(true);
              await fetch(`${API_BASE}/api/courses/${selectedCourseId}/sync-assignments`, { method: "POST", credentials: "include" });
              fetchAssignments(selectedCourseId);
              setIsSyncing(false);
            }}
            isSyncing={isSyncing}
            selectedAssignmentId={selectedAssignmentId}
            setSelectedAssignmentId={setSelectedAssignmentId}
            assignments={assignments}
            analyzeSubmissions={async () => {
              setIsAnalyzing(true);
              const res = await fetch(`${API_BASE}/api/courses/${selectedCourseId}/assignments/${selectedAssignmentId}/analyze`, { method: "POST", credentials: "include" });
              const data = await res.json();
              setAnalysisData(data);
              setIsAnalyzing(false);
            }}
            isAnalyzing={isAnalyzing}
            analysisData={analysisData}
            aiError={aiError}
            setAiFile={setAiFile}
            handleAiCheck={handleAiCheck}
            aiLoading={aiLoading}
            aiResult={aiResult}
          />
        )}

        {activeTab === "evaluation" && (hasPermission("evaluation", "view") || hasPermission("evaluation", "edit")) && <EvaluationPanel API_BASE={API_BASE} courseId={selectedCourseId} />}
        {activeTab === "timetable" && (hasPermission("timetable", "view") || hasPermission("timetable", "edit")) && <Timetablegenerator courses={courses} />}
      </div>
    </div>
  );
}
