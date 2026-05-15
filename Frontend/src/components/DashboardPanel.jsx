import React from 'react';
import { usePermissions } from '../context/PermissionContext';

const DashboardPanel = ({
  user,
  stats,
  selectedCourseId,
  setSelectedCourseId,
  courses,
  showTargetForm,
  setShowTargetForm,
  targetTopic,
  setTargetTopic,
  targetDate,
  setTargetDate,
  handleAddTarget,
  isSavingTarget,
  targets,
  targetsLoading,
  targetsError,
  toggleTargetStatus,
  formatTargetDate,
  complianceMetrics,
  metricsLoading,
  metricsError,
  generateComplianceReport,
  complianceMessage,
  handleSyncCourses,
  isSyncing,
  syncError
}) => {
  const { hasPermission } = usePermissions();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Institutional Hero Card */}
      <div className="card" style={{ 
        background: 'linear-gradient(135deg, #0e1a25 0%, #1e293b 100%)',
        color: 'white',
        border: 'none'
      }}>
        <div className="card-header">
          <p className="kicker" style={{ color: '#38bdf8' }}>Institutional Insights</p>
          <h2 style={{ fontSize: '2rem', margin: '8px 0', color: 'white' }}>Welcome back, {user?.name || "Educator"}</h2>
          <p style={{ color: '#94a3b8' }}>Real-time overview of academic progress and institutional metrics.</p>
        </div>
        <div className="card-body">
          <div className="metric-grid">
            <div className="meet-stat-card" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
              <p className="metric-label" style={{ color: '#94a3b8' }}>Active Courses</p>
              <p className="metric-value" style={{ color: 'white' }}>{stats?.total_courses || courses.length}</p>
            </div>
            <div className="meet-stat-card" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
              <p className="metric-label" style={{ color: '#94a3b8' }}>System Identities</p>
              <p className="metric-value" style={{ color: 'white' }}>{stats?.total_roles || 0}</p>
            </div>
            <div className="meet-stat-card" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
              <p className="metric-label" style={{ color: '#94a3b8' }}>Syllabus Coverage</p>
              <p className="metric-value" style={{ color: 'white' }}>{complianceMetrics.coCoverage}%</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid">
        {/* Syllabus Control Card */}
        <div className="card">
          <div className="card-header">
            <h3>Syllabus & Target Completion</h3>
            <p>Track progress by unit and upcoming deadlines.</p>
          </div>
          <div className="card-body">
            <div className="input-row">
              <select
                value={selectedCourseId}
                onChange={(e) => setSelectedCourseId(e.target.value)}
                style={{ flex: 1 }}
              >
                <option value="">Select Subject</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>{course.name}</option>
                ))}
              </select>
              {hasPermission('teacher-dashboard', 'edit') && (
                <button
                  className="ghost sm"
                  onClick={() => setShowTargetForm((prev) => !prev)}
                  disabled={!selectedCourseId}
                >
                  {showTargetForm ? "Close" : "+ Add"}
                </button>
              )}
            </div>

            {showTargetForm && (
              <div className="target-form" style={{ marginTop: '15px', padding: '15px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <input
                  placeholder="Enter unit or topic"
                  value={targetTopic}
                  onChange={(e) => setTargetTopic(e.target.value)}
                  style={{ marginBottom: '10px' }}
                />
                <input
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  style={{ marginBottom: '10px' }}
                />
                <button className="primary full" onClick={handleAddTarget} disabled={isSavingTarget}>
                  {isSavingTarget ? "Adding..." : "Add Target"}
                </button>
              </div>
            )}

            <div style={{ marginTop: '20px' }}>
              {targetsLoading ? (
                <p className="hint">Synchronizing targets...</p>
              ) : targets.length > 0 ? (
                <ul className="list">
                  {targets.map((target) => (
                    <li key={target.id}>
                      <div className="target-info">
                        <span style={{ fontWeight: 600 }}>{target.topic}</span>
                      </div>
                      <button
                        className={`status-pill ${target.completed ? "completed" : "pending"}`}
                        onClick={() => toggleTargetStatus(target.id, !target.completed)}
                        disabled={isSavingTarget || !hasPermission('teacher-dashboard', 'edit')}
                      >
                        {target.completed ? "Completed" : "Pending"}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="placeholder">No active targets for this subject.</div>
              )}
            </div>
          </div>
        </div>

        {/* Institutional Compliance Card */}
        <div className="card">
          <div className="card-header">
            <h3>NBA/NAAC Compliance</h3>
            <p>Export mapped CO & PO outcomes for accreditation.</p>
          </div>
          <div className="card-body">
            <div className="metric-grid" style={{ marginBottom: '24px' }}>
              <div style={{ textAlign: 'center', padding: '15px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <p className="metric-label">CO Mapping</p>
                <p className="metric-value" style={{ color: '#0f172a' }}>{complianceMetrics.coCoverage}%</p>
              </div>
              <div style={{ textAlign: 'center', padding: '15px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <p className="metric-label">PO Attainment</p>
                <p className="metric-value" style={{ color: '#0f172a' }}>{complianceMetrics.poMapping}%</p>
              </div>
            </div>
            
            <div className="stack" style={{ gap: '12px' }}>
              {hasPermission('teacher-dashboard', 'view') && (
                <button className="primary full" onClick={generateComplianceReport}>
                  Generate NBA Compliance Report
                </button>
              )}
              {hasPermission('teacher-dashboard', 'edit') && (
                <button className="ghost full" onClick={handleSyncCourses} disabled={isSyncing}>
                  {isSyncing ? "Syncing..." : "Refresh Classroom Roster"}
                </button>
              )}
            </div>
            {complianceMessage && <p className="hint" style={{ textAlign: 'center', marginTop: '12px' }}>{complianceMessage}</p>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPanel;
