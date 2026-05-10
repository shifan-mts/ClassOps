import React from 'react';

export default function AttendanceReport({ report, loading, onRefresh }) {
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
