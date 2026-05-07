import React, { useState, useEffect } from 'react';

export default function FeedbackPanel({ apiBase, courses, courseId, onCourseChange, isSyncing }) {
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState("");
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const [internalComment, setInternalComment] = useState("");
  const [grade, setGrade] = useState("");
  const [syncToGoogle, setSyncToGoogle] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const selectedSubmission = submissions.find(s => s.id === selectedSubmissionId);

  useEffect(() => {
    if (courseId) {
      fetchAssignments(courseId);
    } else {
      setAssignments([]);
      setSelectedAssignmentId("");
    }
  }, [courseId]);

  useEffect(() => {
    if (courseId && selectedAssignmentId) {
      fetchSubmissions();
    } else {
      setSubmissions([]);
      setSelectedSubmissionId("");
    }
  }, [selectedAssignmentId]);

  useEffect(() => {
    if (selectedSubmission) {
      setInternalComment(selectedSubmission.internal_comment || "");
      setGrade(selectedSubmission.assignedGrade || "");
      setSyncToGoogle(false);
    } else {
      setInternalComment("");
      setGrade("");
      setSyncToGoogle(false);
    }
    setError("");
    setSuccessMsg("");
  }, [selectedSubmissionId, submissions]);

  const fetchAssignments = async (cid) => {
    try {
      const res = await fetch(`${apiBase}/api/courses/${cid}/assignments`, { credentials: "include" });
      const data = await res.json();
      if (res.ok) {
        setAssignments(Array.isArray(data) ? data : []);
        if (data.length > 0) {
            setSelectedAssignmentId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch assignments", err);
    }
  };

  const fetchSubmissions = async () => {
    setIsLoading(true);
    setError("");
    try {
      const res = await fetch(`${apiBase}/api/courses/${courseId}/assignments/${selectedAssignmentId}/submissions`, { credentials: "include" });
      const data = await res.json();
      if (res.ok) {
        setSubmissions(Array.isArray(data) ? data : []);
      } else {
        setError(data.error || "Failed to fetch submissions");
      }
    } catch (err) {
      setError("Error connecting to server to fetch submissions");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveFeedback = async () => {
    if (!selectedSubmission) return;
    setIsSaving(true);
    setError("");
    setSuccessMsg("");
    
    try {
      const payload = {
        internal_comment: internalComment,
        grade: grade ? parseFloat(grade) : null,
        sync_to_google: syncToGoogle,
        google_submission_id: selectedSubmission.id
      };
      
      const res = await fetch(`${apiBase}/api/courses/${courseId}/assignments/${selectedAssignmentId}/submissions/${selectedSubmission.userId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg(syncToGoogle ? "Feedback saved and synced to Google Classroom!" : "Draft feedback saved internally.");
        // Update local state without refetching all
        setSubmissions(prev => prev.map(sub => {
          if (sub.id === selectedSubmission.id) {
            return {
              ...sub,
              internal_comment: data.feedback.internal_comment,
              synced_comment: data.feedback.synced_comment,
              assignedGrade: data.feedback.grade
            };
          }
          return sub;
        }));
      } else {
        setError(data.error || "Failed to save feedback");
      }
    } catch (err) {
      setError("Error connecting to server to save feedback");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="stack">
      <div className="card">
        <div className="card-header">
          <h3>Feedback & Grading</h3>
          <p>Grade and comment on student submissions, optionally syncing back to Google Classroom.</p>
        </div>
        <div className="card-body">
          <div className="input-row">
            <select
              value={courseId}
              onChange={(e) => onCourseChange(e.target.value)}
            >
              <option value="">Select Subject</option>
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <select
              value={selectedAssignmentId}
              onChange={(e) => setSelectedAssignmentId(e.target.value)}
              disabled={!courseId}
            >
              <option value="">Select Assignment</option>
              {assignments.map(a => (
                <option key={a.id} value={a.id}>{a.title}</option>
              ))}
            </select>
          </div>

          <div className="input-row" style={{ marginTop: '12px' }}>
            <select
              value={selectedSubmissionId}
              onChange={(e) => setSelectedSubmissionId(e.target.value)}
              disabled={!selectedAssignmentId || submissions.length === 0}
            >
              <option value="">Select Student Submission</option>
              {submissions.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} {s.roll_number ? `(${s.roll_number})` : ''} - {s.state}
                </option>
              ))}
            </select>
            {isLoading && <span className="hint">Loading submissions...</span>}
          </div>

          {selectedSubmission && (
            <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <h4 style={{ margin: '0 0 12px 0' }}>Submission Details</h4>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span><strong>Student:</strong> {selectedSubmission.name}</span>
                  <span><strong>Status:</strong> {selectedSubmission.state}</span>
                </div>
                {selectedSubmission.synced_comment && (
                  <div style={{ marginTop: '8px', padding: '8px', background: '#fff', borderRadius: '6px', fontSize: '0.9rem' }}>
                    <strong>Previously Synced Comment:</strong> {selectedSubmission.synced_comment}
                  </div>
                )}
              </div>

              <div className="input-row" style={{ alignItems: 'flex-start' }}>
                <textarea 
                  placeholder="Write your feedback here..."
                  value={internalComment}
                  onChange={(e) => setInternalComment(e.target.value)}
                  style={{ flex: 1, padding: '12px', borderRadius: '12px', border: '1px solid #cdd8e3', minHeight: '120px', fontFamily: 'inherit' }}
                />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '200px' }}>
                  <input 
                    type="number" 
                    placeholder="Grade (e.g. 95)" 
                    value={grade}
                    onChange={(e) => setGrade(e.target.value)}
                  />
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem' }}>
                    <input 
                      type="checkbox" 
                      checked={syncToGoogle}
                      onChange={(e) => setSyncToGoogle(e.target.checked)}
                      style={{ width: 'auto', margin: 0 }}
                    />
                    Sync to Google Classroom
                  </label>
                  <button className="primary" onClick={handleSaveFeedback} disabled={isSaving}>
                    {isSaving ? "Saving..." : (syncToGoogle ? "Sync & Save" : "Save Draft")}
                  </button>
                </div>
              </div>
              
              {error && <p className="hint" style={{ color: '#c53030' }}>{error}</p>}
              {successMsg && <p className="hint" style={{ color: '#0f8a5f' }}>{successMsg}</p>}
            </div>
          )}
          
          {!selectedSubmission && selectedAssignmentId && !isLoading && submissions.length > 0 && (
            <div className="placeholder">
              Select a student to view and grade their submission.
            </div>
          )}
          
          {selectedAssignmentId && !isLoading && submissions.length === 0 && (
            <div className="placeholder">
              No submissions found for this assignment.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
