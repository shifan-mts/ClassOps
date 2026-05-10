import React from 'react';

const OverviewPanel = ({
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
  return (
    <section className="grid">
      <div className="card">
        <div className="card-header">
          <h3>Material & Target Completion</h3>
          <p>Track progress by unit and upcoming deadlines.</p>
        </div>
        <div className="card-body">
          <div className="input-row">
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
            >
              <option value="">Select Subject</option>
              {courses.map((course) => (
                <option key={course.id} value={course.id}>{course.name}</option>
              ))}
            </select>
            <button
              className="ghost"
              onClick={() => setShowTargetForm((prev) => !prev)}
              disabled={!selectedCourseId}
            >
              {showTargetForm ? "Close" : "+ Add Syllabus Target"}
            </button>
          </div>

          {showTargetForm && (
            <div className="target-form">
              <input
                placeholder="Enter unit or topic (e.g., Unit 3: Databases)"
                value={targetTopic}
                onChange={(e) => setTargetTopic(e.target.value)}
              />
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
              <button className="primary" onClick={handleAddTarget} disabled={isSavingTarget}>
                {isSavingTarget ? "Adding..." : "Add Target"}
              </button>
              <button className="ghost" onClick={() => setShowTargetForm(false)} disabled={isSavingTarget}>
                Cancel
              </button>
            </div>
          )}

          {targetsLoading ? (
            <p>Loading syllabus targets...</p>
          ) : targets.length > 0 ? (
            <ul className="list">
              {targets.map((target) => (
                <li key={target.id}>
                  <div className="target-info">
                    <span>{target.topic}</span>
                    {target.course_name && <span className="target-course">{target.course_name}</span>}
                  </div>
                  <div className="target-actions">
                    <button
                      className={`status-pill ${target.completed ? "completed" : "pending"}`}
                      onClick={() => toggleTargetStatus(target.id, !target.completed)}
                      disabled={isSavingTarget}
                    >
                      {target.completed
                        ? "Completed"
                        : `Pending${target.date ? ` (Due: ${formatTargetDate(target.date)})` : ""}`}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="placeholder">
              {selectedCourseId ? "No targets added yet. Add a syllabus target to get started." : "Select a subject to view syllabus targets."}
            </div>
          )}

          {targetsError && <p className="hint" style={{ color: "#c53030" }}>{targetsError}</p>}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>NBA/NAAC Metrics Data</h3>
          <p>Export mapped CO & PO outcomes for compliance.</p>
        </div>
        <div className="card-body">
          <div className="metric-grid">
            <div>
              <p className="metric-label">CO Coverage</p>
              <p className="metric-value">{complianceMetrics.coCoverage}%</p>
            </div>
            <div>
              <p className="metric-label">PO Mapping</p>
              <p className="metric-value">{complianceMetrics.poMapping}%</p>
            </div>
          </div>
          {metricsLoading && <p className="hint">Analyzing metrics...</p>}
          {metricsError && <p className="hint" style={{ color: "#c53030" }}>{metricsError}</p>}
          {complianceMetrics.status && <p className="hint">Status: {complianceMetrics.status}</p>}
          <p className="hint">Based on completed syllabus targets and attendance records.</p>
          <button className="primary full" onClick={generateComplianceReport}>
            Generate NBA Compliance Report
          </button>
          {complianceMessage && <p className="hint">{complianceMessage}</p>}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Google Classroom Courses</h3>
          <p>Synced courses from your connected Google Classroom account.</p>
        </div>
        <div className="card-body">
          <button className="primary" onClick={handleSyncCourses} disabled={isSyncing}>
            {isSyncing ? "Syncing..." : "Sync Courses"}
          </button>
          {syncError && <p className="error">{syncError}</p>}
          {courses.length > 0 ? (
            <ul className="list">
              {courses.map((course) => (
                <li key={course.id || course.google_course_id}>
                  <span>{course.name}</span>
                  {course.google_course_id && (
                    <span className="status">{course.google_course_id}</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div className="placeholder">
              No courses loaded yet. Click "Sync Courses" to fetch them.
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default OverviewPanel;
