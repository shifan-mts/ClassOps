import React from 'react';

const Header = ({ user, handleLogout, handleSignIn, isSyncing }) => {
  return (
    <header className="header">
      <div>
        <p className="kicker">Teacher Workflow Automation</p>
        <h1>ClassOps</h1>
        <p className="subtitle">Keep syllabus targets, compliance metrics, and AI tools in one focused workspace.</p>
      </div>
      <div className="auth-section">
        {user ? (
          <div className="user-profile">
            {user.picture && <img src={user.picture} alt={user.name} className="avatar" />}
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <button className="ghost sm" onClick={handleLogout}>Logout</button>
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
