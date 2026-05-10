import React from 'react';
import AttendanceReport from './AttendanceReport';

const AttendancePanel = ({
  selectedCourseId,
  setSelectedCourseId,
  courses,
  attendanceDate,
  setAttendanceDate,
  syncStudents,
  isSyncing,
  saveAttendance,
  students,
  attendanceRecords,
  handleAttendanceChange,
  report,
  isReportLoading,
  fetchReport,
  onViewFeedback
}) => {
  return (
    <section className="stack">
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3>Subject-wise Attendance</h3>
            <p>Log presence for the selected subject and date.</p>
          </div>
          <button className="ghost" onClick={() => onViewFeedback(null)} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
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
                        onClick={() => onViewFeedback(s.google_student_id || s.id)}
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
  );
};

export default AttendancePanel;
