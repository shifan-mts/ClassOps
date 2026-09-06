import React, { useEffect, useRef, useState } from 'react';

const POLL_INTERVAL_MS = 20000;
const MEETING_CODE_PATTERN = /([a-z]{3}-[a-z]{4}-[a-z]{3})/i;
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const DEFAULT_PERIOD_WINDOWS = [
  { label: "8-9 AM", startHour: 8, endHour: 9 },
  { label: "9-10 AM", startHour: 9, endHour: 10 },
  { label: "10-11 AM", startHour: 10, endHour: 11 },
  { label: "11-12 PM", startHour: 11, endHour: 12 },
  { label: "12-1 PM", startHour: 12, endHour: 13 },
  { label: "1-2 PM", startHour: 13, endHour: 14 },
  { label: "2-3 PM", startHour: 14, endHour: 15 },
  { label: "3-4 PM", startHour: 15, endHour: 16 }
];

const extractMeetingCode = (value) => {
  if (!value) return "";
  const match = String(value).trim().match(MEETING_CODE_PATTERN);
  return match ? match[1].toLowerCase() : "";
};

const buildMeetLink = (meetingCode) => {
  const normalizedCode = extractMeetingCode(meetingCode);
  return normalizedCode ? `https://meet.google.com/${normalizedCode}` : "";
};

const formatTimestamp = (value, fallback = "Still in meeting") => {
  if (!value) return fallback;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
};

const formatDuration = (value) => {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(2) : "0.00";
};

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

export default function MeetAttendancePanel({
  apiBase,
  courses,
  courseId,
  onCourseChange,
  students,
  timetableData,
  periodTimings,
  onAttendanceMapped,
  onSyncStudents,
  isSyncing
}) {
  const pollTimeoutRef = useRef(null);
  const [meetingLink, setMeetingLink] = useState("");
  const [meetingCode, setMeetingCode] = useState("");
  const [meetingSource, setMeetingSource] = useState("unavailable");
  const [meetingWarning, setMeetingWarning] = useState("");
  const [meetingStatus, setMeetingStatus] = useState("");
  const [meetingError, setMeetingError] = useState("");
  const [attendanceRows, setAttendanceRows] = useState([]);
  const [allParticipantRows, setAllParticipantRows] = useState([]);
  const [unmatchedRows, setUnmatchedRows] = useState([]);
  const [summary, setSummary] = useState({
    conferenceRecord: "",
    meetingEnded: false,
    participantCount: 0,
    livePresentCount: 0,
    conferenceStartTime: null,
    conferenceEndTime: null
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const periodWindows = Array.isArray(periodTimings) && periodTimings.length > 0 ? periodTimings : DEFAULT_PERIOD_WINDOWS;
  const activeCourses = courses.filter((course) => Number(course?.hours_per_week || 0) > 0);
  const now = new Date();
  const todayName = DAYS[now.getDay()];
  const currentPeriodIndex = periodWindows.findIndex((period) => now.getHours() >= period.startHour && now.getHours() < period.endHour);
  const currentSlot = currentPeriodIndex >= 0
    ? activeCourses
        .map((course) => {
          const slot = timetableData?.[course.id]?.[todayName]?.[currentPeriodIndex];
          return slot ? { courseId: String(course.id), courseName: course.name, periodIndex: currentPeriodIndex, periodLabel: periodWindows[currentPeriodIndex].label, slot } : null;
        })
        .find(Boolean)
    : null;
  const selectedCourseTodaySlots = courseId
    ? periodWindows
        .map((period, index) => {
          const slot = timetableData?.[courseId]?.[todayName]?.[index];
          return slot ? { periodIndex: index, periodLabel: period.label, slot } : null;
        })
        .filter(Boolean)
    : [];
  const nextSelectedSlot = selectedCourseTodaySlots.find((slot) => slot.periodIndex > currentPeriodIndex);

  useEffect(() => {
    if (!activeCourses.length) {
      return;
    }
    const isSelectedCourseActive = activeCourses.some((course) => String(course.id) === String(courseId));
    if (!isSelectedCourseActive) {
      onCourseChange(String(activeCourses[0].id));
    }
  }, [activeCourses, courseId, onCourseChange]);

  const stopPolling = () => {
    if (pollTimeoutRef.current) {
      window.clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  };

  const resetLiveState = () => {
    stopPolling();
    setAttendanceRows([]);
    setAllParticipantRows([]);
    setUnmatchedRows([]);
    setSummary({
      conferenceRecord: "",
      meetingEnded: false,
      participantCount: 0,
      livePresentCount: 0,
      conferenceStartTime: null,
      conferenceEndTime: null
    });
    setMeetingStatus("");
    setMeetingError("");
    setIsTracking(false);
  };

  const handleClearPreviousRecord = () => {
    resetLiveState();
    setMeetingStatus("Previous Meet report cleared. You can start a fresh recording now.");
  };

  const handlePrepareNewRecord = () => {
    resetLiveState();
    setMeetingStatus("Ready for a new Meet session. Click `Join & Track` when the teacher starts the class.");
  };

  const loadMeetingConfig = async (targetCourseId) => {
    if (!targetCourseId) return;
    setMeetingError("");
    try {
      const res = await fetch(`${apiBase}/api/courses/${targetCourseId}/meeting-config`, {
        credentials: "include"
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Failed to load meeting settings.");
      }

      setMeetingLink(data?.meetLink || "");
      setMeetingCode(data?.meetingCode || "");
      setMeetingSource(data?.source || "unavailable");
      setMeetingWarning(data?.warning || "");
    } catch (err) {
      setMeetingError(err?.message || "Failed to load meeting settings.");
    }
  };

  useEffect(() => {
    resetLiveState();
    if (!courseId) {
      setMeetingLink("");
      setMeetingCode("");
      setMeetingSource("unavailable");
      setMeetingWarning("");
      return undefined;
    }

    loadMeetingConfig(courseId);
    return () => stopPolling();
  }, [courseId]);

  const scheduleNextPoll = (nextMeetingCode) => {
    stopPolling();
    pollTimeoutRef.current = window.setTimeout(() => {
      pollAttendance(nextMeetingCode);
    }, POLL_INTERVAL_MS);
  };

  const saveMeetingConfig = async () => {
    if (!courseId) {
      throw new Error("Please select a subject first.");
    }

    const normalizedCode = extractMeetingCode(meetingCode || meetingLink);
    const normalizedLink = meetingLink.trim() || buildMeetLink(normalizedCode);
    if (!normalizedCode) {
      throw new Error("Enter the Google Meet link or the meeting code for this subject.");
    }

    setIsSaving(true);
    try {
      const res = await fetch(`${apiBase}/api/courses/${courseId}/meeting-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          meet_link: normalizedLink,
          meeting_code: normalizedCode
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Failed to save meeting settings.");
      }

      setMeetingLink(data?.meetLink || normalizedLink);
      setMeetingCode(data?.meetingCode || normalizedCode);
      setMeetingSource(data?.source || "stored_config");
      setMeetingWarning(data?.warning || "");
      return data;
    } finally {
      setIsSaving(false);
    }
  };

  const pollAttendance = async (targetMeetingCode) => {
    if (!courseId) return;
    setIsPolling(true);
    setMeetingError("");

    try {
      const res = await fetch(
        `${apiBase}/api/courses/${courseId}/meet/attendance?meeting_code=${encodeURIComponent(targetMeetingCode)}`,
        { credentials: "include" }
      );
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Failed to fetch the Meet attendance report.");
      }

      const nextAttendance = Array.isArray(data?.attendance) ? data.attendance : [];
      const nextAllParticipants = Array.isArray(data?.allParticipants) ? data.allParticipants : nextAttendance;
      const nextUnmatched = Array.isArray(data?.unmatchedParticipants) ? data.unmatchedParticipants : [];
      setAttendanceRows(nextAttendance);
      setAllParticipantRows(nextAllParticipants);
      setUnmatchedRows(nextUnmatched);
      setSummary({
        conferenceRecord: data?.conferenceRecord || "",
        meetingEnded: Boolean(data?.meetingEnded),
        participantCount: Number(data?.participantCount || 0),
        livePresentCount: Number(data?.livePresentCount || 0),
        conferenceStartTime: data?.conferenceStartTime || null,
        conferenceEndTime: data?.conferenceEndTime || null
      });

      if (data?.status === "unavailable") {
        setIsTracking(false);
        setMeetingStatus(data?.message || "The latest Meet report is not available right now.");
        return;
      }

      if (data?.meetingEnded) {
        stopPolling();
        setIsTracking(false);
        setMeetingStatus(
          nextAttendance.length > 0
            ? "Meet attendance finished. You can export the session or map it into the attendance screen."
            : "The meeting ended, but no roster-matched participants were returned."
        );
        onAttendanceMapped?.(nextAttendance);
      } else {
        setIsTracking(true);
        setMeetingStatus(
          data?.conferenceRecord
            ? "Live tracking is active. The dashboard will refresh automatically every 20 seconds."
            : "Waiting for Google Meet to create the conference record."
        );
        scheduleNextPoll(targetMeetingCode);
      }
    } catch (err) {
      stopPolling();
      setIsTracking(false);
      setMeetingStatus("");
      setMeetingError(err?.message || "Failed to fetch the Meet attendance report.");
    } finally {
      setIsPolling(false);
    }
  };

  const handleJoinAndTrack = async () => {
    try {
      const savedConfig = await saveMeetingConfig();
      const normalizedCode = extractMeetingCode(savedConfig?.meetingCode || meetingCode || meetingLink);
      const normalizedLink = savedConfig?.meetLink || meetingLink.trim() || buildMeetLink(normalizedCode);
      if (!normalizedLink) {
        throw new Error("Could not determine the Google Meet link for this subject.");
      }

      setAttendanceRows([]);
      setAllParticipantRows([]);
      setUnmatchedRows([]);
      setSummary({
        conferenceRecord: "",
        meetingEnded: false,
        participantCount: 0,
        livePresentCount: 0,
        conferenceStartTime: null,
        conferenceEndTime: null
      });
      setIsTracking(true);
      setMeetingStatus("Meet opened. ClassOps is starting live tracking now.");
      window.open(normalizedLink, "_blank", "noopener,noreferrer");
      await pollAttendance(normalizedCode);
    } catch (err) {
      setMeetingError(err?.message || "Could not start Meet tracking.");
    }
  };

  const handleExport = async (format) => {
    if (!courseId) {
      setMeetingError("Please select a subject first.");
      return;
    }

    const normalizedCode = extractMeetingCode(meetingCode || meetingLink);
    if (!normalizedCode) {
      setMeetingError("Save a Meet code before exporting.");
      return;
    }

    setIsExporting(true);
    setMeetingError("");
    try {
      const res = await fetch(
        `${apiBase}/api/courses/${courseId}/meet/attendance/export?meeting_code=${encodeURIComponent(normalizedCode)}&format=${format}`,
        { credentials: "include" }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error || "Failed to export the Meet attendance report.");
      }

      const blob = await res.blob();
      const selectedCourse = courses.find((course) => course.id.toString() === courseId);
      const safeCourse = (selectedCourse?.name || "course").replace(/[^a-z0-9]+/gi, "_").toLowerCase();
      const extension = format === "csv" ? "csv" : "json";
      downloadBlob(blob, `meet_attendance_${safeCourse}_${normalizedCode}.${extension}`);
    } catch (err) {
      setMeetingError(err?.message || "Failed to export the Meet attendance report.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <section className="stack">
      <div className="card">
        <div className="card-header">
          <h3>Google Meet Live Tracking</h3>
          <p>Choose a subject, save its Meet link, and keep watching joins, rejoins, and total duration live.</p>
        </div>
        <div className="card-body">
          <div className="input-row">
            <select value={courseId} onChange={(event) => onCourseChange(event.target.value)}>
              <option value="">Select Subject</option>
              {activeCourses.map((course) => (
                <option key={course.id} value={course.id}>{course.name}</option>
              ))}
            </select>
            {currentSlot && (
              <button className="ghost" onClick={() => onCourseChange(currentSlot.courseId)}>
                Use Current Class
              </button>
            )}
            <button className="ghost" onClick={onSyncStudents} disabled={!courseId || isSyncing}>
              {isSyncing ? "Syncing..." : "Sync Roster"}
            </button>
            <button className="ghost" onClick={() => pollAttendance(extractMeetingCode(meetingCode || meetingLink))} disabled={!courseId || isPolling || !extractMeetingCode(meetingCode || meetingLink)}>
              {isPolling ? "Refreshing..." : "Refresh Live"}
            </button>
          </div>

          {currentSlot && (
            <p className="hint">
              Current timetable slot: {currentSlot.courseName} during {currentSlot.periodLabel}. You can use `Join & Track` for this class right now.
            </p>
          )}
          {!currentSlot && (
            <p className="hint">No class is scheduled in the timetable right now. You can still start Meet tracking manually if needed.</p>
          )}
          {courseId && selectedCourseTodaySlots.length > 0 && (
            <p className="hint">
              Today's scheduled periods for this subject: {selectedCourseTodaySlots.map((slot) => slot.periodLabel).join(", ")}.
              {nextSelectedSlot ? ` Next slot starts at ${nextSelectedSlot.periodLabel}.` : ""}
            </p>
          )}
          {courseId && selectedCourseTodaySlots.length === 0 && (
            <p className="hint">This subject has no timetable slot scheduled for {todayName}.</p>
          )}

          <div className="input-row">
            <input
              style={{ flex: 2 }}
              placeholder="https://meet.google.com/abc-defg-hij"
              value={meetingLink}
              onChange={(event) => {
                setMeetingLink(event.target.value);
                if (!meetingCode) {
                  setMeetingCode(extractMeetingCode(event.target.value));
                }
              }}
              disabled={!courseId || isSaving}
            />
            <input
              style={{ flex: 1 }}
              placeholder="abc-defg-hij"
              value={meetingCode}
              onChange={(event) => setMeetingCode(extractMeetingCode(event.target.value))}
              disabled={!courseId || isSaving}
            />
            <button className="ghost" onClick={saveMeetingConfig} disabled={!courseId || isSaving}>
              {isSaving ? "Saving..." : "Save Meet"}
            </button>
            <button className="primary" onClick={handleJoinAndTrack} disabled={!courseId || isSaving || isPolling}>
              {isPolling ? "Checking..." : isTracking ? "Tracking..." : "Join & Track"}
            </button>
          </div>

          <div className="metric-grid">
            <div className="meet-stat-card">
              <p className="metric-label">Participants</p>
              <p className="metric-value">{summary.participantCount}</p>
            </div>
            <div className="meet-stat-card">
              <p className="metric-label">Live Now</p>
              <p className="metric-value">{summary.livePresentCount}</p>
            </div>
            <div className="meet-stat-card">
              <p className="metric-label">Visible Rows</p>
              <p className="metric-value">{allParticipantRows.length}</p>
            </div>
            <div className="meet-stat-card">
              <p className="metric-label">Meeting Status</p>
              <p className="metric-value meet-status-value">{summary.meetingEnded ? "Ended" : isTracking ? "Live" : "Ready"}</p>
            </div>
          </div>

          {meetingSource !== "unavailable" && (
            <p className="hint">Source: {meetingSource === "classroom_api" ? "Classroom API" : "Saved course setting"}.</p>
          )}
          {summary.conferenceStartTime && (
            <p className="hint">
              Started: {formatTimestamp(summary.conferenceStartTime, "Not started")}
              {summary.conferenceEndTime ? ` | Ended: ${formatTimestamp(summary.conferenceEndTime, "Still live")}` : ""}
            </p>
          )}
          {meetingWarning && <p className="hint" style={{ color: "#975a16" }}>{meetingWarning}</p>}
          {meetingStatus && <p className="hint">{meetingStatus}</p>}
          {meetingError && <p className="error">{meetingError}</p>}

          <div className="input-row">
            <button className="ghost" onClick={() => handleExport("json")} disabled={!allParticipantRows.length || isExporting}>
              {isExporting ? "Exporting..." : "Download JSON"}
            </button>
            <button className="ghost" onClick={() => handleExport("csv")} disabled={!allParticipantRows.length || isExporting}>
              {isExporting ? "Exporting..." : "Download CSV"}
            </button>
            <button className="ghost" onClick={handleClearPreviousRecord} disabled={!allParticipantRows.length && !summary.conferenceRecord}>
              Clear Previous Record
            </button>
            <button className="ghost" onClick={handlePrepareNewRecord}>
              Record New Session
            </button>
            {isTracking && (
              <button
                className="ghost"
                onClick={() => {
                  stopPolling();
                  setIsTracking(false);
                  setMeetingStatus("Live tracking stopped.");
                }}
              >
                Stop Tracking
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Live Student Timeline</h3>
          <p>Only matched roster students are shown here, ordered in ascending name order.</p>
        </div>
        <div className="card-body">
          {attendanceRows.length > 0 ? (
            <table className="attendance-table">
              <thead>
                <tr>
                  <th>Roll Number</th>
                  <th>Student</th>
                  <th>Email</th>
                  <th>First Join</th>
                  <th>Last Leave</th>
                  <th style={{ textAlign: "right" }}>Sessions</th>
                  <th style={{ textAlign: "right" }}>Rejoins</th>
                  <th style={{ textAlign: "right" }}>Duration (min)</th>
                  <th style={{ textAlign: "right" }}>Live</th>
                </tr>
              </thead>
              <tbody>
                {attendanceRows.map((row) => (
                  <tr key={`${row.email}-${row.rollNumber || row.studentName}`}>
                    <td>{row.rollNumber || "-"}</td>
                    <td>{row.studentName}</td>
                    <td>{row.email || "No email resolved"}</td>
                    <td>{formatTimestamp(row.joinTime, "-")}</td>
                    <td>{formatTimestamp(row.leaveTime)}</td>
                    <td style={{ textAlign: "right" }}>{row.sessionCount ?? 0}</td>
                    <td style={{ textAlign: "right" }}>{row.rejoinCount ?? 0}</td>
                    <td style={{ textAlign: "right" }}>{formatDuration(row.totalDurationMinutes)}</td>
                    <td style={{ textAlign: "right" }}>
                      <span className={`status ${row.activeNow ? "success-bg" : "warn-bg"}`}>
                        {row.activeNow ? "In Meet" : "Left"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="placeholder">
              No Meet attendance data yet. Save a subject Meet link and click `Join & Track` to start live tracking.
            </div>
          )}
        </div>
      </div>

      {unmatchedRows.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>Guest Participants</h3>
            <p>These participants were seen in Meet but do not match your roster after excluded teacher accounts were removed.</p>
          </div>
          <div className="card-body">
            <table className="attendance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>First Join</th>
                  <th>Last Leave</th>
                  <th style={{ textAlign: "right" }}>Sessions</th>
                  <th style={{ textAlign: "right" }}>Rejoins</th>
                  <th style={{ textAlign: "right" }}>Duration (min)</th>
                </tr>
              </thead>
              <tbody>
                {unmatchedRows.map((row, index) => (
                  <tr key={`${row.email || "unknown"}-${index}`}>
                    <td>{row.studentName}</td>
                    <td>{row.email || "No email resolved"}</td>
                    <td>{formatTimestamp(row.joinTime, "-")}</td>
                    <td>{formatTimestamp(row.leaveTime)}</td>
                    <td style={{ textAlign: "right" }}>{row.sessionCount ?? 0}</td>
                    <td style={{ textAlign: "right" }}>{row.rejoinCount ?? 0}</td>
                    <td style={{ textAlign: "right" }}>{formatDuration(row.totalDurationMinutes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
