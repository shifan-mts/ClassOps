import React from 'react';

const Header = ({ user, handleLogout, handleSignIn, isSyncing }) => {
  const isStudent = user?.role === 'student';
  
  return (
    <header className="header">
      <div>
        <p className="kicker">
          {isStudent ? "Student Learning Dashboard" : "Teacher Workflow Automation"}
        </p>
        <h1>ClassOps</h1>
        <p className="subtitle">
          {isStudent 
            ? "Your centralized hub for assignments, timetables, and classroom materials." 
            : "Keep syllabus targets, compliance metrics, and AI tools in one focused workspace."}
        </p>
      </div>
      <div className="auth-section">
        {user ? (
          <div className="user-profile">
            {user.picture ? (
              <img 
                src={user.picture} 
                alt={user.name} 
                className="avatar" 
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="avatar fallback" style={{ 
                background: '#0f172a', 
                color: '#fff', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.8rem'
              }}>
                {user.name?.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className="status-pill completed" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                  {user.role}
                </span>
                <button className="ghost sm" onClick={handleLogout}>Logout</button>
              </div>
            </div>
          </div>
        ) : (
          <button className="primary" onClick={handleSignIn} disabled={isSyncing}>
            {isSyncing ? "Connecting..." : "Sign in with Google"}
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;
