import React, { useState, useEffect } from 'react';

export default function AdminDashboard({ API_BASE }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('student');
  const [addLoading, setAddLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, { credentials: 'include' });
      const data = await res.json();
      if (res.ok) {
        setUsers(data);
      } else {
        setError(data.error || 'Failed to load users');
      }
    } catch (err) {
      setError('Error connecting to server');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    
    setAddLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: email.trim(), role })
      });
      const data = await res.json();
      if (res.ok) {
        setEmail('');
        setRole('student');
        fetchUsers();
      } else {
        alert(data.error || 'Failed to add user');
      }
    } catch (err) {
      alert('Error adding user');
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteUser = async (id) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${id}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok) {
        fetchUsers();
      } else {
        alert(data.error || 'Failed to delete user');
      }
    } catch (err) {
      alert('Error deleting user');
    }
  };

  return (
    <section className="grid">
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <h3>Admin Dashboard - User Management</h3>
          <p>Add teachers and students to allow them to log into the application.</p>
        </div>
        <div className="card-body">
          <form onSubmit={handleAddUser} className="input-row" style={{ marginBottom: '20px' }}>
            <input 
              type="email" 
              placeholder="User Email (e.g. teacher@college.edu)" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
              <option value="admin">Admin</option>
            </select>
            <button type="submit" className="primary" disabled={addLoading}>
              {addLoading ? 'Adding...' : 'Add User'}
            </button>
          </form>

          {loading ? (
            <p>Loading users...</p>
          ) : error ? (
            <p className="error" style={{ color: 'red' }}>{error}</p>
          ) : (
            <table className="attendance-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.email}</td>
                    <td><span className={`status-pill ${u.role === 'admin' ? 'completed' : u.role === 'teacher' ? 'pending' : ''}`}>{u.role}</span></td>
                    <td>
                      <button 
                        className="ghost sm" 
                        onClick={() => handleDeleteUser(u.id)}
                        disabled={u.email === 'angelinehephzibahj@gmail.com'}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan="4" style={{ textAlign: 'center' }}>No users found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </section>
  );
}
