import { useState, useEffect } from "react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const PERIODS = ["8–9 AM", "9–10 AM", "10–11 AM", "11–12 PM", "12–1 PM", "1–2 PM", "2–3 PM", "3–4 PM"];
const API_BASE = "http://localhost:5000";

const PALETTES = [
  { bg: "#dbeafe", border: "#3b82f6", text: "#1e3a8a" },
  { bg: "#dcfce7", border: "#22c55e", text: "#14532d" },
  { bg: "#fef3c7", border: "#f59e0b", text: "#78350f" },
  { bg: "#fce7f3", border: "#ec4899", text: "#831843" },
  { bg: "#ede9fe", border: "#8b5cf6", text: "#4c1d95" },
  { bg: "#ffedd5", border: "#f97316", text: "#7c2d12" },
  { bg: "#cffafe", border: "#06b6d4", text: "#164e63" },
  { bg: "#fdf4ff", border: "#c026d3", text: "#4a044e" },
  { bg: "#fff7ed", border: "#ea580c", text: "#431407" },
  { bg: "#f0fdf4", border: "#16a34a", text: "#052e16" },
];
const colCache = {}; let colIdx = 0;
function sc(s) { if (!colCache[s]) colCache[s] = PALETTES[colIdx++ % PALETTES.length]; return colCache[s]; }

// ─── Defaults ─────────────────────────────────────────────────────────────────
const INIT_TEACHER = {
  name: "Teacher Profile",
  subjects: [],
  available: { Monday: [], Tuesday: [], Wednesday: [], Thursday: [], Friday: [] },
};
const INIT_CLASSES = [];

// ─── Shared styles ─────────────────────────────────────────────────────────────
const labelStyle = { display: "block", marginBottom: 4, fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.06em" };
const inputStyle = { width: "100%", padding: "9px 12px", borderRadius: 8, border: "1.5px solid #e2e8f0", fontSize: 14, outline: "none", boxSizing: "border-box" };
const btnPrimary = { padding: "8px 16px", borderRadius: 8, background: "#0ea5e9", color: "#fff", border: "none", fontWeight: 600, cursor: "pointer", fontSize: 13 };
const btnSecondary = { padding: "9px 20px", borderRadius: 8, background: "#f1f5f9", color: "#475569", border: "none", fontWeight: 600, cursor: "pointer", fontSize: 13 };
const btnSmall = { padding: "5px 12px", borderRadius: 7, background: "#f8fafc", border: "1.5px solid #e2e8f0", color: "#475569", cursor: "pointer", fontSize: 12, fontWeight: 600 };

// ─── Availability Grid ────────────────────────────────────────────────────────
function AvailGrid({ available, onChange }) {
  function toggle(day, p) {
    const cur = available[day] || [];
    const next = cur.includes(p) ? cur.filter(x => x !== p) : [...cur, p].sort((a, b) => a - b);
    onChange({ ...available, [day]: next });
  }
  function toggleDay(day) {
    const cur = available[day] || [];
    onChange({ ...available, [day]: cur.length === PERIODS.length ? [] : PERIODS.map((_, i) => i) });
  }
  return (
    <div style={{ overflowX: "auto", marginTop: 10 }}>
      <table style={{ borderCollapse: "collapse", fontSize: 11, width: "100%" }}>
        <thead>
          <tr>
            <th style={{ padding: "4px 8px", textAlign: "left", color: "#64748b", fontWeight: 600, fontSize: 11 }}>Day</th>
            {PERIODS.map((p, i) => <th key={i} style={{ padding: "4px 3px", color: "#64748b", fontWeight: 500, whiteSpace: "nowrap", fontSize: 10 }}>{p}</th>)}
            <th style={{ padding: "4px 6px", color: "#94a3b8", fontSize: 10, fontWeight: 500 }}>All</th>
          </tr>
        </thead>
        <tbody>
          {DAYS.map((day, di) => (
            <tr key={day}>
              <td style={{ padding: "3px 8px", fontWeight: 600, color: "#334155", fontSize: 11, whiteSpace: "nowrap" }}>{DAY_SHORT[di]}</td>
              {PERIODS.map((_, pi) => {
                const on = (available[day] || []).includes(pi);
                return (
                  <td key={pi} style={{ padding: "3px 3px", textAlign: "center" }}>
                    <button onClick={() => toggle(day, pi)} style={{
                      width: 22, height: 22, borderRadius: 4, border: "1.5px solid", cursor: "pointer",
                      backgroundColor: on ? "#0ea5e9" : "#f1f5f9",
                      borderColor: on ? "#0284c7" : "#cbd5e1", transition: "all 0.12s"
                    }} />
                  </td>
                );
              })}
              <td style={{ padding: "3px 6px", textAlign: "center" }}>
                <button onClick={() => toggleDay(day)} style={{
                  width: 22, height: 22, borderRadius: 4, border: "1.5px solid #cbd5e1",
                  cursor: "pointer", background: "#f8fafc", fontSize: 11, color: "#64748b"
                }} title="Toggle all">✓</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Profile Modal ────────────────────────────────────────────────────────────
function ProfileModal({ teacher, onSave, onClose }) {
  const [name, setName] = useState(teacher.name || "");
  const [courses, setCourses] = useState(teacher.courses || []);
  const [available, setAvailable] = useState(teacher.availability || { Monday: [], Tuesday: [], Wednesday: [], Thursday: [], Friday: [] });

  function updateHours(id, h) {
    setCourses(courses.map(c => c.id === id ? { ...c, hours: parseInt(h) || 1 } : c));
  }

  function save() {
    if (!name.trim()) { alert("Enter your name"); return; }
    onSave({ name: name.trim(), availability: available, courses: courses });
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ background: "#fff", borderRadius: 18, padding: 28, width: "100%", maxWidth: 660, maxHeight: "90vh", overflowY: "auto", boxShadow: "0 30px 70px rgba(0,0,0,0.25)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 22 }}>
          <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: "#0f172a" }}>My Profile & Availability</h3>
          <button onClick={onClose} style={{ background: "#f1f5f9", border: "none", borderRadius: 8, width: 32, height: 32, cursor: "pointer", fontSize: 16, color: "#64748b" }}>×</button>
        </div>

        <label style={labelStyle}>Your Name</label>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Mr. Sharma"
          style={{ ...inputStyle, marginBottom: 18 }} />

        <label style={labelStyle}>Subject Hour Requirements</label>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 22 }}>
            {courses.map(c => (
                <div key={c.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 10, border: "1.5px solid #e2e8f0", background: "#f8fafc" }}>
                    <span style={{ flex: 1, fontWeight: 700, color: "#334155", fontSize: 13 }}>{c.name}</span>
                    <input type="number" value={c.hours} onChange={e => updateHours(c.id, e.target.value)} min={1} max={10}
                        style={{ width: 40, padding: "3px 6px", borderRadius: 6, border: "1px solid #cbd5e1", background: "#fff", fontSize: 12, textAlign: "center", fontWeight: 700 }} />
                    <span style={{ fontSize: 11, color: "#64748b" }}>hrs/wk</span>
                </div>
            ))}
            {courses.length === 0 && <p style={{ color: "#94a3b8", fontSize: 12 }}>Sync courses from Classroom to set requirements.</p>}
        </div>

        <label style={labelStyle}>My Weekly Availability</label>
        <p style={{ margin: "0 0 6px", fontSize: 11, color: "#94a3b8" }}>Blue = available. Click ✓ to toggle a full day.</p>
        <AvailGrid available={available} onChange={setAvailable} />

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 24 }}>
          <button onClick={onClose} style={btnSecondary}>Cancel</button>
          <button onClick={save} style={{ ...btnPrimary, background: "#0f172a", padding: "9px 24px", fontSize: 13 }}>Save Profile</button>
        </div>
      </div>
    </div>
  );
}

// ─── Class Card ───────────────────────────────────────────────────────────────
function ClassCard({ cls }) {
  return (
    <div style={{ background: "#fff", borderRadius: 14, padding: 18, border: "1.5px solid #e2e8f0", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div>
          <div style={{ fontWeight: 700, color: "#0f172a", fontSize: 15 }}>{cls.name}</div>
          <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>{cls.hours} periods/week required</div>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 10px", borderRadius: 8, border: `1.5px solid ${sc(cls.name).border}`, background: sc(cls.name).bg }}>
              <span style={{ flex: 1, fontWeight: 700, color: sc(cls.name).text, fontSize: 12 }}>{cls.name}</span>
              <span style={{ fontSize: 11, color: sc(cls.name).text, background: "rgba(255,255,255,0.6)", padding: "1px 8px", borderRadius: 10, fontWeight: 700 }}>{cls.hours} hrs/wk</span>
            </div>
      </div>
    </div>
  );
}

// ─── Timetable View ───────────────────────────────────────────────────────────
function TimetableView({ tt, classes, teacher, onRegenerate }) {
  const [view, setView] = useState("mine");
  const [selCls, setSelCls] = useState(classes[0]?.id);

  function buildMyGrid() {
    const grid = {};
    for (const d of DAYS) { grid[d] = {}; }
    for (const c of classes)
      for (const d of DAYS)
        for (let p = 0; p < PERIODS.length; p++) {
          const e = tt[c.id]?.[d]?.[p];
          if (e) grid[d][p] = { ...e, cid: c.id };
        }
    return grid;
  }

  const myGrid = buildMyGrid();
  const cls = classes.find(c => c.id === selCls);

  function buildPrintHTML() {
    let html = `<h1>${teacher.name} — Weekly Timetable</h1>`;
    html += `<h2>My Schedule</h2>`;
    html += `<table><thead><tr><th class="left">Period</th>${DAYS.map(d => `<th>${d}</th>`).join("")}</tr></thead><tbody>`;
    for (let p = 0; p < PERIODS.length; p++) {
      html += `<tr><td class="period">${PERIODS[p]}</td>`;
      for (const d of DAYS) {
        const e = myGrid[d]?.[p];
        const avail = (teacher.availability?.[d] || []).includes(p);
        html += e
          ? `<td><div class="cls">${e.className}</div><div class="sub">${e.sub}</div></td>`
          : avail ? `<td style="color:#d1fae5;font-size:11px;">free</td>`
            : `<td style="color:#e2e8f0;">—</td>`;
      }
      html += `</tr>`;
    }
    html += `</tbody></table>`;
    html += `<h2>By Class</h2>`;
    for (const c of classes) {
      html += `<p style="font-weight:700;font-size:13px;margin:12px 0 4px;">${c.name}</p>`;
      html += `<table><thead><tr><th class="left">Period</th>${DAYS.map(d => `<th>${d}</th>`).join("")}</tr></thead><tbody>`;
      for (let p = 0; p < PERIODS.length; p++) {
        html += `<tr><td class="period">${PERIODS[p]}</td>`;
        for (const d of DAYS) {
          const e = tt[c.id]?.[d]?.[p];
          html += e ? `<td class="cls">${e.sub}</td>` : `<td style="color:#e2e8f0;">—</td>`;
        }
        html += `</tr>`;
      }
      html += `</tbody></table>`;
    }
    return html;
  }

  function handlePrint() {
    const w = window.open("", "_blank");
    w.document.write(`<html><head><title>${teacher.name} — Timetable</title><style>
      *{box-sizing:border-box;} body{font-family:Georgia,serif;margin:0;padding:24px;color:#0f172a;}
      h1{font-size:20px;margin:0 0 4px;} h2{font-size:15px;margin:20px 0 8px;color:#334155;}
      table{width:100%;border-collapse:collapse;margin-bottom:16px;}
      th{background:#0f172a;color:#fff;padding:9px 10px;font-size:12px;text-align:center;}
      th.left{text-align:left;}
      td{border:1px solid #e2e8f0;padding:7px 9px;font-size:12px;text-align:center;vertical-align:middle;}
      td.period{text-align:left;background:#f8fafc;font-weight:700;white-space:nowrap;}
      .cls{font-weight:700;font-size:12px;} .sub{font-size:11px;color:#64748b;}
      @media print{body{padding:10px;}}
    </style></head><body>${buildPrintHTML()}</body></html>`);
    w.document.close(); w.print();
  }

  const thStyle = { padding: "11px 10px", background: "#0f172a", color: "#fff", fontWeight: 700, fontSize: 12, textAlign: "center" };
  const tdBase = { padding: 6, textAlign: "center", borderBottom: "1px solid #f1f5f9", borderRight: "1px solid #f1f5f9" };

  return (
    <div>
      {/* Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18, flexWrap: "wrap", gap: 10 }}>
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={() => setView("mine")} style={{ padding: "7px 16px", borderRadius: 8, background: view === "mine" ? "#0f172a" : "#f1f5f9", color: view === "mine" ? "#fff" : "#475569", border: "none", fontWeight: 600, cursor: "pointer", fontSize: 13 }}>My Schedule</button>
          <button onClick={() => setView("byclass")} style={{ padding: "7px 16px", borderRadius: 8, background: view === "byclass" ? "#0f172a" : "#f1f5f9", color: view === "byclass" ? "#fff" : "#475569", border: "none", fontWeight: 600, cursor: "pointer", fontSize: 13 }}>By Class</button>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={onRegenerate} style={{ padding: "7px 14px", borderRadius: 8, background: "#f1f5f9", color: "#334155", border: "1.5px solid #e2e8f0", fontWeight: 600, cursor: "pointer", fontSize: 12 }}>🔄 Regenerate</button>
          <button onClick={handlePrint} style={{ padding: "7px 14px", borderRadius: 8, background: "#059669", color: "#fff", border: "none", fontWeight: 600, cursor: "pointer", fontSize: 12 }}>🖨️ Print</button>
        </div>
      </div>

      {/* MY SCHEDULE */}
      {view === "mine" && (
        <div style={{ overflowX: "auto", borderRadius: 12, border: "1.5px solid #e2e8f0", boxShadow: "0 2px 16px rgba(0,0,0,0.05)" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 600 }}>
            <thead>
              <tr>
                <th style={{ ...thStyle, textAlign: "left", borderRadius: "10px 0 0 0", padding: "11px 16px" }}>Period</th>
                {DAYS.map((d, i) => <th key={d} style={{ ...thStyle, borderRadius: i === 4 ? "0 10px 0 0" : 0 }}>{d}</th>)}
              </tr>
            </thead>
            <tbody>
              {PERIODS.map((per, p) => {
                const anyAvail = DAYS.some(d => (teacher.availability?.[d] || []).includes(p));
                return (
                  <tr key={p} style={{ background: !anyAvail ? "#fafafa" : p % 2 === 0 ? "#fff" : "#fafcff" }}>
                    <td style={{ ...tdBase, textAlign: "left", padding: "10px 16px", fontWeight: 700, color: !anyAvail ? "#cbd5e1" : "#334155", fontSize: 12, borderRight: "2px solid #e2e8f0", whiteSpace: "nowrap" }}>
                      {per}
                    </td>
                    {DAYS.map(day => {
                      const e = myGrid[day]?.[p];
                      const avail = (teacher.availability?.[day] || []).includes(p);
                      const c = e ? sc(e.sub) : null;
                      return (
                        <td key={day} style={{ ...tdBase, background: !avail ? "#fafafa" : "transparent" }}>
                          {e ? (
                            <div style={{ padding: "6px 8px", borderRadius: 8, border: `1.5px solid ${c.border}`, background: c.bg }}>
                              <div style={{ fontWeight: 700, color: c.text, fontSize: 12 }}>{e.className}</div>
                              <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>{e.sub}</div>
                            </div>
                          ) : avail ? (
                            <span style={{ fontSize: 11, color: "#bbf7d0", fontWeight: 500 }}>free</span>
                          ) : (
                            <span style={{ fontSize: 10, color: "#e2e8f0" }}>—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* BY CLASS */}
      {view === "byclass" && (
        <div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
            {classes.map(c => (
              <button key={c.id} onClick={() => setSelCls(c.id)} style={{ padding: "6px 14px", borderRadius: 8, background: selCls === c.id ? "#0f172a" : "#f8fafc", color: selCls === c.id ? "#fff" : "#475569", border: `1.5px solid ${selCls === c.id ? "#0f172a" : "#e2e8f0"}`, fontWeight: 600, cursor: "pointer", fontSize: 13 }}>
                {c.name}
              </button>
            ))}
          </div>
          {cls && (
            <div style={{ overflowX: "auto", borderRadius: 12, border: "1.5px solid #e2e8f0", boxShadow: "0 2px 16px rgba(0,0,0,0.05)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 600 }}>
                <thead>
                  <tr>
                    <th style={{ ...thStyle, textAlign: "left", borderRadius: "10px 0 0 0", padding: "11px 16px" }}>Period</th>
                    {DAYS.map((d, i) => <th key={d} style={{ ...thStyle, borderRadius: i === 4 ? "0 10px 0 0" : 0 }}>{d}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {PERIODS.map((per, p) => (
                    <tr key={p} style={{ background: p % 2 === 0 ? "#fff" : "#fafcff" }}>
                      <td style={{ ...tdBase, textAlign: "left", padding: "10px 16px", fontWeight: 700, color: "#334155", fontSize: 12, borderRight: "2px solid #e2e8f0", whiteSpace: "nowrap" }}>{per}</td>
                      {DAYS.map(day => {
                        const e = tt[cls.id]?.[day]?.[p];
                        const c = e ? sc(e.sub) : null;
                        return (
                          <td key={day} style={tdBase}>
                            {e ? (
                              <div style={{ padding: "6px 8px", borderRadius: 8, border: `1.5px solid ${c.border}`, background: c.bg }}>
                                <div style={{ fontWeight: 700, color: c.text, fontSize: 12 }}>{e.sub}</div>
                              </div>
                            ) : <span style={{ color: "#e2e8f0", fontSize: 18 }}>—</span>}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function TimetableGenerator() {
  const [tab, setTab] = useState("classes");
  const [teacher, setTeacher] = useState(INIT_TEACHER);
  const [classes, setClasses] = useState(INIT_CLASSES);
  const [result, setResult] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [genErr, setGenErr] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchProfile();
    fetchTimetable();
  }, []);

  const fetchProfile = async () => {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/profile`, { credentials: "include" });
        const data = await res.json();
        if (res.ok) {
            setTeacher({
                name: data.name,
                availability: data.availability,
                courses: data.courses
            });
            setClasses(data.courses);
        }
    } catch (err) {
        console.error("Fetch profile error:", err);
    }
  };

  const fetchTimetable = async () => {
    try {
        const res = await fetch(`${API_BASE}/api/timetable`, { credentials: "include" });
        const data = await res.json();
        if (res.ok && data.timetable) {
            setResult(Object.keys(data.timetable).length > 0 ? data.timetable : null);
            if (Object.keys(data.timetable).length > 0) setTab("timetable");
        }
    } catch (err) {
        console.error("Fetch timetable error:", err);
    }
  };

  const saveProfile = async (updatedTeacher) => {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: updatedTeacher.name,
                availability: updatedTeacher.availability,
                courses: updatedTeacher.courses
            }),
            credentials: "include"
        });
        if (res.ok) {
            setTeacher(updatedTeacher);
            setClasses(updatedTeacher.courses);
            setProfileOpen(false);
            alert("Profile saved!");
        }
    } catch (err) {
        console.error("Save profile error:", err);
        alert("Error saving profile");
    }
  };

  async function generate() {
    if (classes.length === 0) { alert("Add at least one class first (Sync from Dashboard)"); return; }
    
    setGenErr(null); setLoading(true);
    try {
        const res = await fetch(`${API_BASE}/api/timetable/generate`, {
            method: "POST",
            credentials: "include"
        });
        const data = await res.json();
        if (res.ok) {
            await fetchTimetable();
            setTab("timetable");
        } else {
            setGenErr(data.error || "Generation failed");
        }
    } catch (err) {
        setGenErr("Error: " + err.message);
    } finally {
        setLoading(false);
    }
  }

  const totalAvail = Object.values(teacher.availability || {}).reduce((s, v) => s + (v?.length || 0), 0);
  const totalNeeded = classes.reduce((s, c) => s + (c.hours || 0), 0);
  const feasible = totalAvail >= totalNeeded;

  const tabs = [
    { id: "classes", label: `🏫 My Classes (${classes.length})` },
    { id: "timetable", label: "📅 Timetable" },
  ];

  return (
    <div style={{ background: "#fff", borderRadius: 22, boxShadow: "0 20px 45px rgba(15, 25, 35, 0.08)", border: "1px solid #edf2f7", padding: "24px", fontFamily: "'Segoe UI', system-ui, sans-serif", width: "100%", boxSizing: "border-box" }}>

      <div style={{ padding: "0 0 20px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, borderBottom: "1.5px solid #e2e8f0", marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: "#0f172a" }}>Timetable Planner</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b" }}>Manage your weekly schedule for synced courses</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button onClick={() => setProfileOpen(true)} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 14px", borderRadius: 10, background: "#f1f5f9", border: "1.5px solid #e2e8f0", cursor: "pointer" }}>
            <div style={{ textAlign: "left" }}>
              <div style={{ color: "#0f172a", fontWeight: 700, fontSize: 12 }}>{teacher.name}</div>
              <div style={{ color: "#64748b", fontSize: 10 }}>{totalAvail} slots available</div>
            </div>
            <span style={{ color: "#475569", fontSize: 12, marginLeft: 2 }}>✎</span>
          </button>
          <button onClick={generate} disabled={loading}
            style={{ padding: "10px 22px", borderRadius: 10, background: loading ? "#1e293b" : "#0f172a", color: "#fff", border: "none", fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", fontSize: 13 }}>
            {loading ? "⏳..." : "⚡ Generate"}
          </button>
        </div>
      </div>

      <div style={{ background: "transparent", padding: "0 0 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: 4 }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              style={{ padding: "12px 16px", background: "none", border: "none", borderBottom: `3px solid ${tab === t.id ? "#f59e0b" : "transparent"}`, color: tab === t.id ? "#0f172a" : "#64748b", fontWeight: tab === t.id ? 700 : 500, cursor: "pointer", fontSize: 13, transition: "all 0.15s" }}>
              {t.label}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: "#0f172a" }}>{totalNeeded}</div>
            <div style={{ fontSize: 10, color: "#94a3b8" }}>hrs needed/wk</div>
          </div>
          <div style={{ width: 1, height: 28, background: "#e2e8f0" }} />
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: feasible ? "#059669" : "#dc2626" }}>{totalAvail}</div>
            <div style={{ fontSize: 10, color: "#94a3b8" }}>slots available/wk</div>
          </div>
          {!feasible && totalNeeded > 0 && (
            <div style={{ padding: "3px 10px", borderRadius: 6, background: "#fff1f2", border: "1px solid #fecaca", color: "#dc2626", fontSize: 11, fontWeight: 600 }}>
              ⚠️ not enough slots
            </div>
          )}
        </div>
      </div>

      {genErr && (
        <div style={{ margin: "16px 28px 0", padding: "12px 16px", borderRadius: 10, background: "#fff1f2", border: "1.5px solid #fecaca", color: "#b91c1c", fontSize: 13, fontWeight: 500 }}>
          ⚠️ {genErr}
        </div>
      )}

      <div style={{ padding: "10px 0", maxWidth: "100%", margin: "0" }}>

        {tab === "classes" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 17, fontWeight: 800, color: "#0f172a" }}>My Classes</h2>
                <p style={{ margin: "4px 0 0", fontSize: 12, color: "#64748b" }}>Manage the hours needed for each of your synced subjects.</p>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 14 }}>
              {classes.map(c => <ClassCard key={c.id} cls={c} />)}
              {classes.length === 0 && (
                <div style={{ gridColumn: "1/-1", textAlign: "center", padding: "60px 20px", color: "#94a3b8" }}>
                  <div style={{ fontSize: 40, marginBottom: 10 }}>🏫</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "#334155", marginBottom: 6 }}>No classes yet</div>
                  <p style={{ fontSize: 13, margin: 0 }}>Sync with Google Classroom in the Dashboard header to see your courses here.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "timetable" && (
          <div>
            {result ? (
              <div>
                <div style={{ marginBottom: 20 }}>
                  <h2 style={{ margin: "0 0 4px", fontSize: 17, fontWeight: 800, color: "#0f172a" }}>Generated Timetable</h2>
                  <p style={{ margin: 0, fontSize: 12, color: "#64748b" }}>
                    <strong>My Schedule</strong> — where you need to be each period. &nbsp;|&nbsp; <strong>By Class</strong> — each class's subject timetable.
                  </p>
                </div>
                <TimetableView tt={result} classes={classes} teacher={teacher} onRegenerate={generate} />
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "70px 20px" }}>
                <div style={{ fontSize: 52, marginBottom: 14 }}>📅</div>
                <div style={{ fontSize: 17, fontWeight: 800, color: "#334155", marginBottom: 8 }}>No timetable generated yet</div>
                <p style={{ color: "#64748b", fontSize: 13, maxWidth: 340, margin: "0 auto 24px" }}>
                  Set your course hour requirements and profile availability, then hit Generate.
                </p>
                <button onClick={generate} style={{ padding: "12px 32px", borderRadius: 12, background: "#f59e0b", color: "#0f172a", border: "none", fontWeight: 800, cursor: "pointer", fontSize: 15 }}>
                  ⚡ Generate Schedule
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {profileOpen && <ProfileModal teacher={teacher} onSave={saveProfile} onClose={() => setProfileOpen(false)} />}
    </div>
  );
}