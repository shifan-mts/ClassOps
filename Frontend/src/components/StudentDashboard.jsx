import React, { useState, useEffect } from 'react';
import { usePermissions } from '../context/PermissionContext';

const StudentDashboard = ({ API_BASE, onReadFeedback }) => {
  const { hasPermission } = usePermissions();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const [showTodayOnly, setShowTodayOnly] = useState(true);

  // Evaluation Form State
  const [showEvalForm, setShowEvalForm] = useState(false);
  const [evalRatings, setEvalRatings] = useState({});
  const [isSubmittingEval, setIsSubmittingEval] = useState(false);

  const evalQuestions = [
    { id: 'Q1', text: 'The course objectives were clearly explained.' },
    { id: 'Q2', text: 'The syllabus content was relevant to the programme.' },
    { id: 'Q3', text: 'The course content helped in improving subject knowledge.' },
    { id: 'Q4', text: 'The prescribed textbook / reference materials were useful.' },
    { id: 'Q5', text: 'The course improved my understanding of the subject and it helped in achieving learning outcomes.' },
    { id: 'Q6', text: 'Internal assessments reflected the taught syllabus.' },
    { id: 'Q7', text: 'Assignments / tests supported learning effectively.' },
    { id: 'Q8', text: 'Evaluation methods were fair and transparent.' },
    { id: 'Q9', text: 'The course improved problem-solving / analytical ability.' },
    { id: 'Q10', text: 'The course helped in achieving the intended learning outcomes.' },
  ];

  const handleEvalChange = (qId, value) => {
    setEvalRatings(prev => ({ ...prev, [qId]: parseInt(value) }));
  };

  const submitEvaluation = async () => {
    if (Object.keys(evalRatings).length < 10) {
      alert("Please answer all questions before submitting.");
      return;
    }
    setIsSubmittingEval(true);
    try {
      const res = await fetch(`${API_BASE}/api/student/evaluation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: selectedCourseId,
          ratings: evalRatings
        }),
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok) {
        alert("Evaluation submitted successfully! Thank you for your feedback.");
        setShowEvalForm(false);
        setEvalRatings({});
      } else {
        alert(data.error || "Failed to submit evaluation.");
      }
    } catch (err) {
      alert("Error submitting evaluation.");
    } finally {
      setIsSubmittingEval(false);
    }
  };

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/student/dashboard`, {
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }
        const data = await response.json();
        setDashboardData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, [API_BASE]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#4f6073' }}>
        <h2>Loading your classroom...</h2>
        <p>Fetching assignments and timetables.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ border: '1px solid #fed7aa', background: '#fff7ed' }}>
        <div className="card-body">
          <p className="status warn">Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) return null;

  const { classrooms, assignments, timetable, user, materials = [] } = dashboardData;

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    // Assuming format HH:MM
    const [h, m] = timeStr.split(':');
    let hours = parseInt(h);
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    return `${hours}:${m} ${ampm}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'No Due Date';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const todayDayName = new Date().toLocaleDateString('en-US', { weekday: 'long' });
  const displayedTimetable = showTodayOnly ? timetable.filter(s => s.day === todayDayName) : timetable;
  const displayedMaterials = selectedCourseId ? materials.filter(m => m.course_id === selectedCourseId) : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* HEADER SECTION */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.7), rgba(255,255,255,0.3))',
        backdropFilter: 'blur(10px)',
        borderRadius: '24px',
        padding: '32px',
        border: '1px solid rgba(255,255,255,0.5)',
        boxShadow: '0 8px 32px rgba(15, 25, 35, 0.05)'
      }}>
        <p className="kicker" style={{ color: '#0f8a5f' }}>ClassOps Native</p>
        <h2 style={{ fontSize: '2.4rem', margin: '0 0 8px', color: '#0e1a25' }}>Welcome, {user.name.split(' ')[0]}!</h2>
        <p style={{ margin: 0, color: '#4f6073', fontSize: '1.1rem' }}>
          {user.dept && user.current_year ? `Department of ${user.dept} • Year ${user.current_year}` : 'Your centralized academic hub.'}
        </p>
      </div>

      {/* TOP GRID: Timetable & Assignments */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '24px' }}>
        
        {/* TIMETABLE */}
        {hasPermission('timetable', 'access') && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3>{showTodayOnly ? "Today's Classes" : "Weekly Timetable"}</h3>
                <p>Your automatically synced classes.</p>
              </div>
              <button 
                onClick={() => setShowTodayOnly(!showTodayOnly)}
                style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '8px', background: '#e2e8f0', color: '#0f172a', border: 'none', cursor: 'pointer', fontWeight: 600 }}
              >
                {showTodayOnly ? "View Weekly" : "View Today"}
              </button>
            </div>
            <div className="card-body">
              {displayedTimetable.length === 0 ? (
                <div className="placeholder">No classes scheduled {showTodayOnly ? 'today' : 'yet'}.</div>
              ) : (
                <div style={{ display: 'grid', gap: '12px' }}>
                  {displayedTimetable.map(slot => (
                    <div key={slot.id} style={{
                      display: 'flex', alignItems: 'center', gap: '16px',
                      padding: '16px', borderRadius: '16px',
                      background: '#f8fafc', border: '1px solid #e2e8f0'
                    }}>
                      <div style={{ minWidth: '80px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#0f172a' }}>{slot.day.substring(0,3)}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{formatTime(slot.start_time)}</div>
                      </div>
                      <div style={{ flex: 1, borderLeft: '3px solid #0e1a25', paddingLeft: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#0f172a' }}>{slot.subject}</div>
                          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>ClassOps Sync Enabled</div>
                        </div>
                        {slot.meet_link && (
                          <button 
                            className="primary" 
                            style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '8px' }}
                            onClick={() => window.open(slot.meet_link, '_blank')}
                          >
                            Join Meet
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              <button className="primary" style={{ marginTop: 'auto' }} onClick={async () => {
                try {
                  const res = await fetch(`${API_BASE}/api/student/calendar/sync`, { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ slots: timetable }),
                    credentials: 'include'
                  });
                  const json = await res.json();
                  alert(json.message || json.error);
                } catch(e) {
                  alert('Sync failed');
                }
              }}>Sync to Google Calendar</button>
            </div>
          </div>
        )}

        {/* ASSIGNMENTS */}
        {hasPermission('student-dashboard', 'view') && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-header">
              <h3>Assignment Tracker</h3>
              <p>Track your pending, submitted, and missing work.</p>
            </div>
            <div className="card-body" style={{ display: 'grid', gap: '20px' }}>
              
              {/* PENDING */}
              <div>
                <h4 style={{ margin: '0 0 10px', fontSize: '0.85rem', textTransform: 'uppercase', color: '#b45309', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }}></span>
                  Pending ({assignments.pending.length})
                </h4>
                <div style={{ display: 'grid', gap: '10px' }}>
                  {assignments.pending.map(a => (
                    <div key={a.id} style={{ padding: '14px', borderRadius: '12px', background: '#fffbeb', border: '1px solid #fef3c7' }}>
                      <div style={{ fontWeight: 600, color: '#92400e', marginBottom: '4px' }}>{a.title}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#b45309' }}>
                        <span>{a.course_name}</span>
                        <span style={{ fontWeight: 700 }}>Due: {formatDate(a.due_date)}</span>
                      </div>
                    </div>
                  ))}
                  {assignments.pending.length === 0 && <div className="placeholder" style={{ padding: '10px' }}>All caught up!</div>}
                </div>
              </div>

              {/* MISSING */}
              {assignments.missing.length > 0 && (
                <div>
                  <h4 style={{ margin: '0 0 10px', fontSize: '0.85rem', textTransform: 'uppercase', color: '#9b1c1c', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>
                    Missing ({assignments.missing.length})
                  </h4>
                  <div style={{ display: 'grid', gap: '10px' }}>
                    {assignments.missing.map(a => (
                      <div key={a.id} style={{ padding: '14px', borderRadius: '12px', background: '#fef2f2', border: '1px solid #fee2e2' }}>
                        <div style={{ fontWeight: 600, color: '#991b1b', marginBottom: '4px' }}>{a.title}</div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#b91c1c' }}>
                          <span>{a.course_name}</span>
                          <span style={{ fontWeight: 700 }}>Past Due: {formatDate(a.due_date)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SUBMITTED */}
              <div>
                <h4 style={{ margin: '0 0 10px', fontSize: '0.85rem', textTransform: 'uppercase', color: '#0f8a5f', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>
                  Completed ({assignments.submitted.length})
                </h4>
                <div style={{ display: 'grid', gap: '10px' }}>
                  {assignments.submitted.map(a => (
                    <div key={a.id} style={{ padding: '14px', borderRadius: '12px', background: '#ecfdf5', border: '1px solid #d1fae5', opacity: 0.8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <div style={{ fontWeight: 600, color: '#065f46', marginBottom: '4px', textDecoration: 'line-through' }}>{a.title}</div>
                        {a.score && <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#047857' }}>{a.score}</div>}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ fontSize: '0.8rem', color: '#059669' }}>{a.course_name}</div>
                        <button 
                          className="ghost" 
                          onClick={() => onReadFeedback && onReadFeedback(a.course_id, a.id)}
                          style={{ padding: '4px 8px', fontSize: '0.75rem', background: '#d1fae5', color: '#065f46' }}
                        >
                          Read Feedback
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}
      </div>

      {/* BOTTOM SECTIONS: My Classrooms & Materials */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* MY CLASSROOMS */}
        <div className="card">
          <div className="card-header">
            <h3>My Classrooms</h3>
            <p>Click a class to view its recent materials and announcements.</p>
          </div>
          <div className="card-body">
            {classrooms.length === 0 ? (
              <div className="placeholder">You are not enrolled in any classes yet.</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px' }}>
                {classrooms.map(c => (
                  <div key={c.id} 
                    onClick={() => {
                      if (selectedCourseId !== c.id) {
                        setSelectedCourseId(c.id);
                        setShowEvalForm(false);
                        setEvalRatings({});
                      } else {
                        setSelectedCourseId(null);
                        setShowEvalForm(false);
                      }
                    }}
                    style={{
                    padding: '20px', borderRadius: '18px', 
                    background: selectedCourseId === c.id ? '#1e293b' : '#0e1a25', 
                    color: '#fef7e7',
                    display: 'flex', flexDirection: 'column', gap: '12px',
                    boxShadow: selectedCourseId === c.id ? '0 0 0 4px rgba(59, 130, 246, 0.5)' : '0 10px 25px rgba(14, 26, 37, 0.15)',
                    position: 'relative', overflow: 'hidden', cursor: 'pointer', transition: 'all 0.2s'
                  }}>
                    <div style={{ position: 'absolute', top: '-20px', right: '-20px', width: '100px', height: '100px', background: 'rgba(255,255,255,0.05)', borderRadius: '50%' }}></div>
                    <h4 style={{ margin: 0, fontSize: '1.1rem', lineHeight: 1.3, zIndex: 1 }}>{c.name}</h4>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', zIndex: 1, marginTop: 'auto' }}>
                      <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#3b4c5f', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700 }}>
                        {c.teacher_name.charAt(0)}
                      </div>
                      <span style={{ fontSize: '0.85rem', color: '#a0aec0' }}>{c.teacher_name}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* COURSE MATERIALS */}
        {selectedCourseId && (
          <div className="card" style={{ border: '1px solid #bae6fd', background: '#f0f9ff' }}>
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ color: '#0369a1' }}>Course Materials</h3>
                <p style={{ color: '#0284c7' }}>Showing updates for {classrooms.find(c => c.id === selectedCourseId)?.name}</p>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  onClick={() => setShowEvalForm(!showEvalForm)}
                  style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '8px', background: showEvalForm ? '#e0f2fe' : '#0ea5e9', color: showEvalForm ? '#0369a1' : '#fff', border: 'none', cursor: 'pointer', fontWeight: 700 }}
                >
                  {showEvalForm ? "View Materials" : "Submit Evaluation"}
                </button>
                <button 
                  onClick={() => {
                    setSelectedCourseId(null);
                    setShowEvalForm(false);
                  }}
                  style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '8px', background: '#bae6fd', color: '#0369a1', border: 'none', cursor: 'pointer', fontWeight: 700 }}
                >
                  Close View
                </button>
              </div>
            </div>
            <div className="card-body">
              {showEvalForm ? (
                <div style={{ padding: '20px', background: '#fff', borderRadius: '12px', border: '1px solid #e0f2fe' }}>
                  <h4 style={{ color: '#0f172a', marginBottom: '8px', marginTop: 0 }}>Course Evaluation</h4>
                  <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '24px' }}>Please rate the following on a scale of 1 to 5 (5 being Excellent/Strongly Agree).</p>
                  
                  <div style={{ display: 'grid', gap: '20px' }}>
                    {evalQuestions.map((q, idx) => (
                      <div key={q.id} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ fontWeight: 600, color: '#334155', fontSize: '0.95rem' }}>
                          {idx + 1}. {q.text}
                        </div>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>1</span>
                          {[1, 2, 3, 4, 5].map(val => (
                            <label key={val} style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                              <input 
                                type="radio" 
                                name={q.id} 
                                value={val}
                                checked={evalRatings[q.id] === val}
                                onChange={(e) => handleEvalChange(q.id, e.target.value)}
                                style={{ cursor: 'pointer' }}
                              />
                              <span style={{ fontSize: '0.9rem', fontWeight: evalRatings[q.id] === val ? 700 : 400, color: evalRatings[q.id] === val ? '#0ea5e9' : '#64748b' }}>{val}</span>
                            </label>
                          ))}
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>5</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button 
                    onClick={submitEvaluation}
                    disabled={isSubmittingEval}
                    className="primary"
                    style={{ marginTop: '24px', padding: '10px 20px', width: '100%', borderRadius: '8px', opacity: isSubmittingEval ? 0.7 : 1 }}
                  >
                    {isSubmittingEval ? 'Submitting...' : 'Submit Final Evaluation'}
                  </button>
                </div>
              ) : (
                displayedMaterials.length === 0 ? (
                  <div className="placeholder" style={{ color: '#0284c7' }}>No recent materials found for this class. (Note: Make sure to log out and log back in to grant Google Drive read permissions).</div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                    {displayedMaterials.map(m => (
                      <div key={m.id} style={{
                        padding: '16px', borderRadius: '12px', background: '#fff', border: '1px solid #e0f2fe',
                        display: 'flex', flexDirection: 'column', gap: '8px', boxShadow: '0 4px 6px rgba(14, 165, 233, 0.05)'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '4px 8px', borderRadius: '6px', background: m.type === 'Material' ? '#dbeafe' : '#fef3c7', color: m.type === 'Material' ? '#1e40af' : '#92400e', textTransform: 'uppercase' }}>
                            {m.type}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{formatDate(m.date)}</span>
                        </div>
                        <div style={{ fontWeight: 600, color: '#0f172a', lineHeight: 1.4 }}>{m.title}</div>
                        {m.url && (
                          <a href={m.url} target="_blank" rel="noreferrer" style={{ marginTop: 'auto', display: 'inline-block', fontSize: '0.85rem', color: '#0ea5e9', fontWeight: 600, textDecoration: 'none' }}>
                            View in Classroom &rarr;
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default StudentDashboard;
