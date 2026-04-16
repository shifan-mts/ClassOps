import { useEffect, useMemo, useState } from "react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const DEFAULT_PERIODS = [
  { label: "8-9 AM", startHour: 8, endHour: 9 },
  { label: "9-10 AM", startHour: 9, endHour: 10 },
  { label: "10-11 AM", startHour: 10, endHour: 11 },
  { label: "11-12 PM", startHour: 11, endHour: 12 },
  { label: "12-1 PM", startHour: 12, endHour: 13 },
  { label: "1-2 PM", startHour: 13, endHour: 14 },
  { label: "2-3 PM", startHour: 14, endHour: 15 },
  { label: "3-4 PM", startHour: 15, endHour: 16 }
];
const API_BASE = "http://localhost:5000";

const PALETTES = [
  { bg: "#dbeafe", border: "#3b82f6", text: "#1e3a8a" },
  { bg: "#dcfce7", border: "#22c55e", text: "#14532d" },
  { bg: "#fef3c7", border: "#f59e0b", text: "#78350f" },
  { bg: "#fce7f3", border: "#ec4899", text: "#831843" },
  { bg: "#ede9fe", border: "#8b5cf6", text: "#4c1d95" },
  { bg: "#ffedd5", border: "#f97316", text: "#7c2d12" },
  { bg: "#cffafe", border: "#06b6d4", text: "#164e63" },
  { bg: "#fdf4ff", border: "#c026d3", text: "#4a044e" }
];

const colorCache = {};
let colorIndex = 0;
const getColor = (key) => {
  if (!colorCache[key]) {
    colorCache[key] = PALETTES[colorIndex++ % PALETTES.length];
  }
  return colorCache[key];
};

const INIT_TEACHER = {
  name: "Teacher Profile",
  availability: { Monday: [], Tuesday: [], Wednesday: [], Thursday: [], Friday: [] },
  period_timings: DEFAULT_PERIODS
};

const normalizePeriodTimings = (periodTimings) =>
  DEFAULT_PERIODS.map((defaultPeriod, index) => {
    const current = periodTimings?.[index] || {};
    const startHour = Number.isFinite(Number(current.startHour)) ? Number(current.startHour) : defaultPeriod.startHour;
    const endHour = Number.isFinite(Number(current.endHour)) ? Number(current.endHour) : defaultPeriod.endHour;
    return {
      label: current.label || defaultPeriod.label,
      startHour,
      endHour: endHour > startHour ? endHour : startHour + 1
    };
  });

const buttonPrimary = {
  padding: "10px 18px",
  borderRadius: 10,
  background: "#0f172a",
  color: "#fff",
  border: "none",
  cursor: "pointer",
  fontWeight: 700
};

const buttonGhost = {
  padding: "9px 16px",
  borderRadius: 10,
  background: "#f8fafc",
  color: "#334155",
  border: "1px solid #dbe4ee",
  cursor: "pointer",
  fontWeight: 600
};

function AvailabilityGrid({ available, onChange, periodTimings }) {
  const toggleSlot = (day, period) => {
    const current = available?.[day] || [];
    const next = current.includes(period)
      ? current.filter((value) => value !== period)
      : [...current, period].sort((left, right) => left - right);
    onChange({ ...available, [day]: next });
  };

  const toggleDay = (day) => {
    const current = available?.[day] || [];
    onChange({
      ...available,
      [day]: current.length === periodTimings.length ? [] : periodTimings.map((_, index) => index)
    });
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 680 }}>
        <thead>
          <tr>
            <th style={{ padding: "8px", textAlign: "left", color: "#64748b", fontSize: 12 }}>Day</th>
            {periodTimings.map((period, index) => (
              <th key={index} style={{ padding: "8px 6px", color: "#64748b", fontSize: 11, whiteSpace: "nowrap" }}>
                {period.label}
              </th>
            ))}
            <th style={{ padding: "8px", color: "#64748b", fontSize: 11 }}>All</th>
          </tr>
        </thead>
        <tbody>
          {DAYS.map((day, dayIndex) => (
            <tr key={day}>
              <td style={{ padding: "8px", fontWeight: 700, color: "#334155" }}>{DAY_SHORT[dayIndex]}</td>
              {periodTimings.map((_, periodIndex) => {
                const isAvailable = (available?.[day] || []).includes(periodIndex);
                return (
                  <td key={periodIndex} style={{ padding: "6px", textAlign: "center" }}>
                    <button
                      onClick={() => toggleSlot(day, periodIndex)}
                      style={{
                        width: 24,
                        height: 24,
                        borderRadius: 6,
                        border: `1.5px solid ${isAvailable ? "#0284c7" : "#cbd5e1"}`,
                        background: isAvailable ? "#0ea5e9" : "#fff",
                        cursor: "pointer"
                      }}
                    />
                  </td>
                );
              })}
              <td style={{ padding: "6px", textAlign: "center" }}>
                <button onClick={() => toggleDay(day)} style={buttonGhost}>All</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProfileModal({ teacher, onSave, onClose }) {
  const [name, setName] = useState(teacher.name || "");
  const [courses, setCourses] = useState(teacher.courses || []);
  const [availability, setAvailability] = useState(teacher.availability || INIT_TEACHER.availability);
  const [periodTimings, setPeriodTimings] = useState(normalizePeriodTimings(teacher.period_timings));

  const updateHours = (courseId, value) => {
    const parsed = Number.parseInt(value, 10);
    setCourses((current) =>
      current.map((course) =>
        course.id === courseId ? { ...course, hours: Number.isNaN(parsed) ? 0 : Math.max(parsed, 0) } : course
      )
    );
  };

  const updatePeriod = (index, field, value) => {
    setPeriodTimings((current) =>
      current.map((period, periodIndex) => {
        if (periodIndex !== index) return period;
        if (field === "label") {
          return { ...period, label: value };
        }
        const parsed = Number.parseInt(value, 10);
        return { ...period, [field]: Number.isNaN(parsed) ? period[field] : parsed };
      })
    );
  };

  const handleSave = () => {
    if (!name.trim()) {
      alert("Enter your name");
      return;
    }
    onSave({
      name: name.trim(),
      availability,
      period_timings: normalizePeriodTimings(periodTimings),
      courses
    });
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15, 23, 42, 0.45)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ background: "#fff", width: "100%", maxWidth: 820, maxHeight: "92vh", overflowY: "auto", borderRadius: 20, padding: 28, boxShadow: "0 35px 70px rgba(15, 23, 42, 0.35)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 20, color: "#0f172a" }}>Profile, Timings, and Availability</h3>
            <p style={{ margin: "6px 0 0", color: "#64748b", fontSize: 13 }}>Update timetable hours, edit period timing labels, and mark available slots.</p>
          </div>
          <button onClick={onClose} style={buttonGhost}>Close</button>
        </div>

        <div style={{ display: "grid", gap: 18 }}>
          <div>
            <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "#64748b" }}>Teacher Name</label>
            <input value={name} onChange={(event) => setName(event.target.value)} style={{ width: "100%", padding: "12px 14px", borderRadius: 12, border: "1px solid #d6e0ea" }} />
          </div>

          <div>
            <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "#64748b" }}>Subject Hours</label>
            <div style={{ display: "grid", gap: 10 }}>
              {courses.map((course) => (
                <div key={course.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 12px", border: "1px solid #e2e8f0", borderRadius: 12, background: "#f8fafc" }}>
                  <div style={{ flex: 1, fontWeight: 700, color: "#0f172a" }}>{course.name}</div>
                  <input type="number" min={0} max={10} value={course.hours} onChange={(event) => updateHours(course.id, event.target.value)} style={{ width: 72, padding: "8px 10px", borderRadius: 10, border: "1px solid #cbd5e1" }} />
                  <span style={{ color: "#64748b", fontSize: 12 }}>hrs/wk</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "#64748b" }}>Editable Period Timings</label>
            <div style={{ display: "grid", gap: 10 }}>
              {periodTimings.map((period, index) => (
                <div key={index} style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr", gap: 10 }}>
                  <input value={period.label} onChange={(event) => updatePeriod(index, "label", event.target.value)} style={{ padding: "10px 12px", borderRadius: 10, border: "1px solid #d6e0ea" }} />
                  <input type="number" value={period.startHour} onChange={(event) => updatePeriod(index, "startHour", event.target.value)} style={{ padding: "10px 12px", borderRadius: 10, border: "1px solid #d6e0ea" }} />
                  <input type="number" value={period.endHour} onChange={(event) => updatePeriod(index, "endHour", event.target.value)} style={{ padding: "10px 12px", borderRadius: 10, border: "1px solid #d6e0ea" }} />
                </div>
              ))}
            </div>
          </div>

          <div>
            <label style={{ display: "block", marginBottom: 8, fontSize: 12, fontWeight: 700, color: "#64748b" }}>Weekly Availability</label>
            <p style={{ margin: "0 0 10px", color: "#94a3b8", fontSize: 12 }}>Marked slots are actually available for scheduling and manual placement.</p>
            <AvailabilityGrid available={availability} onChange={setAvailability} periodTimings={periodTimings} />
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 24 }}>
          <button onClick={onClose} style={buttonGhost}>Cancel</button>
          <button onClick={handleSave} style={buttonPrimary}>Save Profile</button>
        </div>
      </div>
    </div>
  );
}

function TimetableView({ timetable, classes, teacher, courseLookup, onRegenerate, onAssignSlot, onOpenMeet }) {
  const [view, setView] = useState("mine");
  const [selectedClassId, setSelectedClassId] = useState(classes[0]?.id || "");
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [selectedCourseForSlot, setSelectedCourseForSlot] = useState("");

  const periodTimings = normalizePeriodTimings(teacher.period_timings);

  useEffect(() => {
    if (!classes.some((course) => String(course.id) === String(selectedClassId))) {
      setSelectedClassId(classes[0]?.id || "");
    }
  }, [classes, selectedClassId]);

  const myGrid = useMemo(() => {
    const grid = {};
    DAYS.forEach((day) => {
      grid[day] = {};
    });
    classes.forEach((course) => {
      DAYS.forEach((day) => {
        periodTimings.forEach((_, periodIndex) => {
          const entry = timetable?.[course.id]?.[day]?.[periodIndex];
          if (entry) {
            grid[day][periodIndex] = { ...entry, cid: course.id };
          }
        });
      });
    });
    return grid;
  }, [classes, timetable, periodTimings]);

  const selectedClass = classes.find((course) => String(course.id) === String(selectedClassId));

  const renderSlotBadge = (entry, available) => {
    if (entry) {
      const palette = getColor(entry.className || entry.sub);
      return (
        <div style={{ padding: "8px", borderRadius: 10, border: `1.5px solid ${palette.border}`, background: palette.bg }}>
          <div style={{ fontWeight: 700, color: palette.text, fontSize: 12 }}>{entry.className}</div>
          <div style={{ fontSize: 10, color: "#475569", marginTop: 3 }}>{entry.sub}</div>
        </div>
      );
    }
    if (available) {
      return <span style={{ fontSize: 11, fontWeight: 700, color: "#0f9f6e" }}>Available</span>;
    }
    return <span style={{ fontSize: 11, color: "#94a3b8" }}>Blocked</span>;
  };

  const handleSlotClick = (day, period, entry) => {
    if (isEditMode) {
      setSelectedSlot({ day, period });
      setSelectedCourseForSlot(entry?.cid ? String(entry.cid) : "");
      return;
    }
    if (entry?.cid) {
      onOpenMeet(entry.cid);
    }
  };

  const saveSelectedSlot = async () => {
    if (!selectedSlot) return;
    await onAssignSlot({ ...selectedSlot, course_id: selectedCourseForSlot ? Number(selectedCourseForSlot) : null });
    setSelectedSlot(null);
  };

  const selectedEntry = selectedSlot ? myGrid?.[selectedSlot.day]?.[selectedSlot.period] : null;

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setView("mine")} style={{ ...buttonGhost, background: view === "mine" ? "#0f172a" : "#f8fafc", color: view === "mine" ? "#fff" : "#334155" }}>My Schedule</button>
          <button onClick={() => setView("byclass")} style={{ ...buttonGhost, background: view === "byclass" ? "#0f172a" : "#f8fafc", color: view === "byclass" ? "#fff" : "#334155" }}>By Class</button>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={() => setIsEditMode((current) => !current)} style={{ ...buttonGhost, background: isEditMode ? "#f59e0b" : "#f8fafc", color: isEditMode ? "#0f172a" : "#334155" }}>
            {isEditMode ? "Stop Manual Edit" : "Manual Allocate"}
          </button>
          <button onClick={onRegenerate} style={buttonGhost}>Regenerate</button>
        </div>
      </div>

      {isEditMode && (
        <div style={{ padding: "14px 16px", borderRadius: 14, border: "1px solid #fcd34d", background: "#fffbeb" }}>
          <div style={{ fontWeight: 700, color: "#92400e", marginBottom: 8 }}>Manual Slot Allocation</div>
          <div style={{ color: "#78350f", fontSize: 12 }}>
            Click any timetable cell to choose the time, then assign a class to that slot or clear it.
          </div>
          {selectedSlot && (
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
              <div style={{ alignSelf: "center", fontSize: 12, color: "#78350f" }}>
                Selected: {selectedSlot.day} | {periodTimings[selectedSlot.period]?.label}
              </div>
              <select value={selectedCourseForSlot} onChange={(event) => setSelectedCourseForSlot(event.target.value)} style={{ padding: "10px 12px", borderRadius: 10, border: "1px solid #d6e0ea" }}>
                <option value="">Clear Slot</option>
                {classes.map((course) => (
                  <option key={course.id} value={course.id}>{course.name}</option>
                ))}
              </select>
              <button onClick={saveSelectedSlot} style={buttonPrimary}>Save Slot</button>
              {selectedEntry && <button onClick={() => { setSelectedCourseForSlot(""); }} style={buttonGhost}>Prepare Clear</button>}
            </div>
          )}
        </div>
      )}

      {view === "mine" && (
        <div style={{ overflowX: "auto", borderRadius: 14, border: "1px solid #e2e8f0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}>
            <thead>
              <tr>
                <th style={{ padding: "12px 14px", textAlign: "left", background: "#0f172a", color: "#fff" }}>Period</th>
                {DAYS.map((day) => (
                  <th key={day} style={{ padding: "12px 10px", background: "#0f172a", color: "#fff" }}>{day}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {periodTimings.map((period, periodIndex) => (
                <tr key={periodIndex} style={{ background: periodIndex % 2 === 0 ? "#fff" : "#fbfdff" }}>
                  <td style={{ padding: "14px", borderBottom: "1px solid #edf2f7", borderRight: "1px solid #edf2f7", fontWeight: 700, color: "#334155", whiteSpace: "nowrap" }}>{period.label}</td>
                  {DAYS.map((day) => {
                    const entry = myGrid?.[day]?.[periodIndex];
                    const available = (teacher.availability?.[day] || []).includes(periodIndex);
                    const isSelected = selectedSlot?.day === day && selectedSlot?.period === periodIndex;
                    return (
                      <td
                        key={`${day}-${periodIndex}`}
                        onClick={() => handleSlotClick(day, periodIndex, entry)}
                        style={{
                          padding: 8,
                          borderBottom: "1px solid #edf2f7",
                          borderRight: "1px solid #edf2f7",
                          background: isSelected ? "#fff7ed" : !available && !entry ? "#f8fafc" : "transparent",
                          cursor: entry?.cid || isEditMode ? "pointer" : "default"
                        }}
                      >
                        {renderSlotBadge(entry, available)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {view === "byclass" && selectedClass && (
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {classes.map((course) => (
              <button key={course.id} onClick={() => setSelectedClassId(course.id)} style={{ ...buttonGhost, background: String(selectedClassId) === String(course.id) ? "#0f172a" : "#f8fafc", color: String(selectedClassId) === String(course.id) ? "#fff" : "#334155" }}>
                {course.name}
              </button>
            ))}
          </div>
          <div style={{ overflowX: "auto", borderRadius: 14, border: "1px solid #e2e8f0" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}>
              <thead>
                <tr>
                  <th style={{ padding: "12px 14px", textAlign: "left", background: "#0f172a", color: "#fff" }}>Period</th>
                  {DAYS.map((day) => (
                    <th key={day} style={{ padding: "12px 10px", background: "#0f172a", color: "#fff" }}>{day}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {periodTimings.map((period, periodIndex) => (
                  <tr key={periodIndex} style={{ background: periodIndex % 2 === 0 ? "#fff" : "#fbfdff" }}>
                    <td style={{ padding: "14px", borderBottom: "1px solid #edf2f7", borderRight: "1px solid #edf2f7", fontWeight: 700, color: "#334155", whiteSpace: "nowrap" }}>{period.label}</td>
                    {DAYS.map((day) => {
                      const entry = timetable?.[selectedClass.id]?.[day]?.[periodIndex];
                      const palette = entry ? getColor(entry.className || entry.sub) : null;
                      return (
                        <td key={`${day}-${periodIndex}`} onClick={() => entry && onOpenMeet(selectedClass.id)} style={{ padding: 8, borderBottom: "1px solid #edf2f7", borderRight: "1px solid #edf2f7", cursor: entry ? "pointer" : "default" }}>
                          {entry ? (
                            <div style={{ padding: "8px", borderRadius: 10, border: `1.5px solid ${palette.border}`, background: palette.bg }}>
                              <div style={{ fontWeight: 700, color: palette.text, fontSize: 12 }}>{entry.sub}</div>
                              <div style={{ fontSize: 10, color: "#475569", marginTop: 3 }}>Open Meet</div>
                            </div>
                          ) : (
                            <span style={{ color: "#94a3b8", fontSize: 11 }}>No class</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TimetableGenerator({ courses: dashboardCourses = [] }) {
  const [tab, setTab] = useState("classes");
  const [teacher, setTeacher] = useState(INIT_TEACHER);
  const [classes, setClasses] = useState([]);
  const [timetable, setTimetable] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const activeClasses = classes.filter((course) => (course.hours || 0) > 0);
  const inactiveClasses = classes.filter((course) => (course.hours || 0) <= 0);
  const courseLookup = useMemo(() => {
    const lookup = {};
    dashboardCourses.forEach((course) => {
      lookup[String(course.id)] = course;
    });
    return lookup;
  }, [dashboardCourses]);

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/teacher/profile`, { credentials: "include" });
      const data = await res.json();
      if (res.ok) {
        setTeacher({
          name: data.name,
          availability: data.availability,
          period_timings: normalizePeriodTimings(data.period_timings),
          courses: data.courses
        });
        setClasses(data.courses || []);
      }
    } catch (err) {
      console.error("Fetch profile error:", err);
    }
  };

  const fetchTimetable = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/timetable`, { credentials: "include" });
      const data = await res.json();
      if (res.ok) {
        setTimetable(data?.timetable && Object.keys(data.timetable).length > 0 ? data.timetable : null);
        if (data?.availability || data?.period_timings) {
          setTeacher((current) => ({
            ...current,
            availability: data.availability || current.availability,
            period_timings: normalizePeriodTimings(data.period_timings || current.period_timings)
          }));
        }
      }
    } catch (err) {
      console.error("Fetch timetable error:", err);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchTimetable();
  }, []);

  const saveProfile = async (payload) => {
    try {
      const res = await fetch(`${API_BASE}/api/teacher/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include"
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error || "Failed to save profile");
      }
      await fetchProfile();
      await fetchTimetable();
      setProfileOpen(false);
    } catch (err) {
      alert(err?.message || "Error saving profile");
    }
  };

  const generate = async () => {
    if (!activeClasses.length) {
      alert("Set hours above 0 for at least one current class before generating the timetable.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/timetable/generate`, {
        method: "POST",
        credentials: "include"
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Generation failed");
      }
      await fetchTimetable();
      setTab("timetable");
    } catch (err) {
      setError(err?.message || "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const assignSlot = async ({ day, period, course_id }) => {
    try {
      const res = await fetch(`${API_BASE}/api/timetable/slot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ day, period, course_id })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || "Could not update the slot.");
      }
      await fetchTimetable();
    } catch (err) {
      alert(err?.message || "Could not update the slot.");
    }
  };

  const openMeetForCourse = (courseId) => {
    const course = courseLookup[String(courseId)];
    const meetLink = course?.meet_link || (course?.meeting_code ? `https://meet.google.com/${course.meeting_code}` : "");
    if (!meetLink) {
      alert("No Meet link is saved for this class yet. Open the Meet tab and save one there first.");
      return;
    }
    window.open(meetLink, "_blank", "noopener,noreferrer");
  };

  const totalAvail = Object.values(teacher.availability || {}).reduce((sum, entries) => sum + (entries?.length || 0), 0);
  const totalNeeded = activeClasses.reduce((sum, course) => sum + (course.hours || 0), 0);
  const feasible = totalAvail >= totalNeeded;

  return (
    <div style={{ background: "#fff", borderRadius: 22, boxShadow: "0 20px 45px rgba(15, 25, 35, 0.08)", border: "1px solid #edf2f7", padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", borderBottom: "1px solid #e2e8f0", paddingBottom: 18, marginBottom: 18 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, color: "#0f172a" }}>Timetable Planner</h2>
          <p style={{ margin: "6px 0 0", color: "#64748b", fontSize: 13 }}>Edit timings, fix availability, manually place slots, and open Meet directly from the timetable.</p>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button onClick={() => setProfileOpen(true)} style={buttonGhost}>Edit Profile & Timings</button>
          <button onClick={generate} disabled={loading} style={{ ...buttonPrimary, opacity: loading ? 0.7 : 1 }}>
            {loading ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 18 }}>
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={() => setTab("classes")} style={{ ...buttonGhost, background: tab === "classes" ? "#0f172a" : "#f8fafc", color: tab === "classes" ? "#fff" : "#334155" }}>Classes ({activeClasses.length})</button>
          <button onClick={() => setTab("timetable")} style={{ ...buttonGhost, background: tab === "timetable" ? "#0f172a" : "#f8fafc", color: tab === "timetable" ? "#fff" : "#334155" }}>Timetable</button>
        </div>
        <div style={{ display: "flex", gap: 18 }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontWeight: 800, color: "#0f172a" }}>{totalNeeded}</div>
            <div style={{ fontSize: 11, color: "#94a3b8" }}>hrs needed</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontWeight: 800, color: feasible ? "#059669" : "#dc2626" }}>{totalAvail}</div>
            <div style={{ fontSize: 11, color: "#94a3b8" }}>available slots</div>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: 16, padding: "12px 14px", borderRadius: 12, background: "#fff1f2", border: "1px solid #fecaca", color: "#b91c1c" }}>
          {error}
        </div>
      )}

      {tab === "classes" && (
        <div style={{ display: "grid", gap: 14 }}>
          <div style={{ color: "#64748b", fontSize: 13 }}>Classes with `0` hours are treated as old and excluded from generation, but you can turn them back on anytime.</div>
          <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
            {activeClasses.map((course) => {
              const palette = getColor(course.name);
              return (
                <div key={course.id} style={{ border: "1px solid #e2e8f0", borderRadius: 16, padding: 18, background: "#fff" }}>
                  <div style={{ fontWeight: 800, color: "#0f172a" }}>{course.name}</div>
                  <div style={{ marginTop: 8, display: "inline-flex", padding: "4px 10px", borderRadius: 999, background: palette.bg, color: palette.text, border: `1px solid ${palette.border}`, fontSize: 12, fontWeight: 700 }}>
                    {course.hours} hrs/wk
                  </div>
                </div>
              );
            })}
          </div>
          {inactiveClasses.length > 0 && (
            <div style={{ padding: "14px 16px", borderRadius: 14, border: "1px solid #e2e8f0", background: "#f8fafc", color: "#64748b", fontSize: 13 }}>
              {inactiveClasses.length} old class{inactiveClasses.length === 1 ? "" : "es"} are currently set to `0` hours.
            </div>
          )}
        </div>
      )}

      {tab === "timetable" && (
        timetable ? (
          <TimetableView
            timetable={timetable}
            classes={activeClasses}
            teacher={teacher}
            courseLookup={courseLookup}
            onRegenerate={generate}
            onAssignSlot={assignSlot}
            onOpenMeet={openMeetForCourse}
          />
        ) : (
          <div style={{ padding: "48px 20px", textAlign: "center", color: "#64748b" }}>
            Generate a timetable or manually allocate slots after setting availability and period timings.
          </div>
        )
      )}

      {profileOpen && <ProfileModal teacher={{ ...teacher, courses: classes }} onSave={saveProfile} onClose={() => setProfileOpen(false)} />}
    </div>
  );
}
