import React, { useState, useEffect } from 'react';
import StudentDashboard from './StudentDashboard';

function AdminDashboard({ API_BASE, user }) {
  const [stats, setStats] = useState({ total_courses: 0, total_roles: 0, total_custom_assignments: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/dashboard/stats`, { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [API_BASE]);

  if (loading) return <div className="card-body">Loading Admin Dashboard...</div>;

  return (
    <div className="grid">
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <h3>Admin Overview</h3>
          <p>Welcome to the global ClassOps dashboard.</p>
        </div>
        <div className="card-body">
          <div className="metric-grid" style={{ marginBottom: '20px' }}>
            <div className="meet-stat-card">
              <p className="metric-label">Total Courses</p>
              <p className="metric-value">{stats.total_courses}</p>
            </div>
            <div className="meet-stat-card">
              <p className="metric-label">System Roles</p>
              <p className="metric-value">{stats.total_roles}</p>
            </div>
            <div className="meet-stat-card">
              <p className="metric-label">Custom Assignments</p>
              <p className="metric-value">{stats.total_custom_assignments}</p>
            </div>
          </div>
          
          <div style={{ background: '#f9fbfd', padding: '20px', borderRadius: '16px', border: '1px solid #e4ecf4' }}>
            <h4 style={{ marginTop: 0, color: '#0e1a25' }}>Quick Actions</h4>
            <ul className="list">
              <li>
                <span><strong>View Any Class:</strong> Navigate to the <em>Overview</em> tab to select and inspect any course's targets and attendance across the college.</span>
              </li>
              <li>
                <span><strong>Manage Roles:</strong> Navigate to the <em>Role Management</em> tab to configure permissions or assign users.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function TeacherDashboard({ API_BASE, user }) {
  const [stats, setStats] = useState({ total_courses: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/dashboard/stats`, { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [API_BASE]);

  if (loading) return <div className="card-body">Loading Dashboard...</div>;

  return (
    <div className="grid">
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <h3>Teacher Dashboard</h3>
          <p>Welcome back, {user?.name || "Teacher"}. Here is your daily summary.</p>
        </div>
        <div className="card-body">
          <div className="metric-grid" style={{ marginBottom: '20px' }}>
            <div className="meet-stat-card">
              <p className="metric-label">Active Courses</p>
              <p className="metric-value">{stats.total_courses}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Upcoming Classes</h3>
          <p>Your schedule for today.</p>
        </div>
        <div className="card-body">
          <div className="placeholder">
            <p className="hint">No upcoming classes scheduled for today.</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Reports</h3>
          <p>Activity and target completions.</p>
        </div>
        <div className="card-body">
          <div className="placeholder">
            <p className="hint">No recent reports available.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardRouter({ API_BASE, user, onReadFeedback }) {
  if (!user) return null;

  if (user.role === 'admin') {
    return <AdminDashboard API_BASE={API_BASE} user={user} />;
  }
  
  if (user.role === 'student') {
    return <StudentDashboard API_BASE={API_BASE} user={user} onReadFeedback={onReadFeedback} />;
  }

  // Fallback for teacher or demo
  return <TeacherDashboard API_BASE={API_BASE} user={user} />;
}
