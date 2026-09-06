import React from 'react';
import AttendanceReport from './AttendanceReport';
import { usePermissions } from '../context/PermissionContext';

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
  handleMarkAllPresent,
  handleExportCSV,
  report,
  isReportLoading,
  fetchReport,
  onViewFeedback
}) => {
  const { hasPermission } = usePermissions();

  const getStatusColor = (status) => {
    switch (status) {
      case "Present": return "#0f8a5f";
      case "Absent": return "#e53e3e";
      case "Late": return "#d69e2e";
      default: return "inherit";
    }
  };

  return (
    <section className="stack">
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3>Subject-wise Attendance</h3>
            <p>Log presence for the selected subject and date.</p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {hasPermission('attendance', 'view') && (
              <button className="ghost" onClick={handleExportCSV} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
                Export CSV
              </button>
            )}
            {hasPermission('evaluation', 'view') && (
              <button className="ghost" onClick={() => onViewFeedback(null)} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
                View Feedback
              </button>
            )}
          </div>
        </div>
        <div className="card-body">
          <div className="input-row" style={{ flexWrap: 'wrap' }}>
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              style={{ minWidth: '200px' }}
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
            {hasPermission('attendance', 'manage') && (
              <button className="ghost" onClick={syncStudents} disabled={isSyncing}>
                {isSyncing ? "Syncing..." : "Sync Roster"}
              </button>
            )}
            {hasPermission('attendance', 'edit') && (
              <button className="ghost" onClick={handleMarkAllPresent} style={{ border: '1px solid #0f8a5f', color: '#0f8a5f' }}>
                Mark All Present
              </button>
            )}
            {hasPermission('attendance', 'edit') && (
              <button className="primary" onClick={saveAttendance}>Save Attendance</button>
            )}
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
                {students.map((s) => {
                  const status = attendanceRecords[s.id] || "Present";
                  return (
                    <tr key={s.id}>
                      <td>{s.roll_number}</td>
                      <td>{s.name}</td>
                      <td>
                        {hasPermission('evaluation', 'view') && (
                          <button 
                            className="ghost sm" 
                            onClick={() => onViewFeedback(s.google_student_id || s.id)}
                          >
                            Grade/Feedback
                          </button>
                        )}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <select
                          disabled={!hasPermission('attendance', 'edit')}
                          value={status}
                          onChange={(e) => handleAttendanceChange(s.id, e.target.value)}
                          style={{ 
                            color: getStatusColor(status), 
                            fontWeight: 'bold',
                            borderColor: getStatusColor(status) + '44'
                          }}
                        >
                          <option value="Present">Present</option>
                          <option value="Absent">Absent</option>
                          <option value="Late">Late</option>
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="placeholder">
              No students found for this subject. Try "Sync Roster" to fetch from Google Classroom.
            </div>
          )}
        </div>
      </div>

      {hasPermission('attendance', 'view') && (
        <AttendanceReport 
          report={report} 
          loading={isReportLoading} 
          onRefresh={fetchReport} 
        />
      )}
    </section>
  );
};

export default AttendancePanel;
