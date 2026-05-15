import React, { useState, useEffect } from 'react';

const MODULES = [
  "overview", "attendance", "meet", "ai-tools", 
  "evaluations", "timetable", "student-dashboard", "admin_settings"
];
const PERMISSIONS = ["access", "view", "edit", "modify"];

export default function AdminPanel({ API_BASE }) {
  const [roles, setRoles] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Role Form
  const [editingRole, setEditingRole] = useState(null);
  const [roleName, setRoleName] = useState("");
  const [rolePerms, setRolePerms] = useState({});

  // Assignment Form
  const [assignEmails, setAssignEmails] = useState("");
  const [assignRole, setAssignRole] = useState("");
  const [selectedEmails, setSelectedEmails] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resRoles, resAssig] = await Promise.all([
        fetch(`${API_BASE}/api/roles`, { credentials: "include" }),
        fetch(`${API_BASE}/api/role-assignments`, { credentials: "include" })
      ]);
      if (resRoles.ok) setRoles(await resRoles.json());
      if (resAssig.ok) setAssignments(await resAssig.json());
    } catch (err) {
      console.error("Failed to fetch admin data", err);
    }
    setLoading(false);
    setSelectedEmails([]); // Reset selection on fetch
  };

  const handleEditRole = (role) => {
    setEditingRole(role);
    setRoleName(role.name);
    setRolePerms(role.permissions || {});
  };

  const handleCreateNewRole = () => {
    setEditingRole({ isNew: true });
    setRoleName("");
    setRolePerms({});
  };

  const togglePermission = (mod, perm) => {
    setRolePerms(prev => {
      const modPerms = prev[mod] ? [...prev[mod]] : [];
      if (modPerms.includes(perm)) {
        return { ...prev, [mod]: modPerms.filter(p => p !== perm) };
      } else {
        return { ...prev, [mod]: [...modPerms, perm] };
      }
    });
  };

  const saveRole = async () => {
    if (!roleName.trim()) return alert("Role name is required");
    const method = editingRole.isNew ? "POST" : "PUT";
    const url = editingRole.isNew ? `${API_BASE}/api/roles` : `${API_BASE}/api/roles/${editingRole.name}`;
    
    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name: roleName.trim(), permissions: rolePerms })
      });
      if (res.ok) {
        setEditingRole(null);
        fetchData();
      } else {
        const data = await res.json();
        alert(data.error || "Failed to save role");
      }
    } catch (err) {
      alert("Error saving role");
    }
  };

  const deleteRole = async (name) => {
    if (!confirm(`Are you sure you want to delete role '${name}'?`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/roles/${name}`, { method: "DELETE", credentials: "include" });
      if (res.ok) fetchData();
      else alert((await res.json()).error);
    } catch (err) {
      alert("Error deleting role");
    }
  };

  const saveAssignments = async () => {
    if (!assignEmails.trim() || !assignRole) return alert("Emails and role are required");
    const emailList = assignEmails.split(/[\n,]+/).map(e => e.trim()).filter(e => e);
    
    try {
      const res = await fetch(`${API_BASE}/api/role-assignments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ emails: emailList, role: assignRole })
      });
      if (res.ok) {
        setAssignEmails("");
        setAssignRole("");
        fetchData();
      } else {
        alert((await res.json()).error);
      }
    } catch (err) {
      alert("Error assigning roles");
    }
  };

  const toggleEmailSelection = (email) => {
    setSelectedEmails(prev => 
      prev.includes(email) ? prev.filter(e => e !== email) : [...prev, email]
    );
  };

  const deleteSelectedAssignments = async () => {
    if (selectedEmails.length === 0) return alert("No users selected.");
    if (!confirm(`Remove assignment for ${selectedEmails.length} users?`)) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/role-assignments/bulk-delete`, { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ emails: selectedEmails })
      });
      if (res.ok) fetchData();
      else alert((await res.json()).error);
    } catch (err) {
      alert("Error removing assignments");
    }
  };

  if (loading) return <div className="card-body">Loading Admin Settings...</div>;

  // Group assignments by role
  const assignmentsByRole = assignments.reduce((acc, curr) => {
    if (!acc[curr.role]) acc[curr.role] = [];
    acc[curr.role].push(curr.email);
    return acc;
  }, {});

  return (
    <div className="grid">
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <h3>Roles & Permissions</h3>
          <p>Define custom roles and manage access levels to different modules.</p>
        </div>
        <div className="card-body">
          {!editingRole ? (
            <>
              <button className="primary" onClick={handleCreateNewRole} style={{ width: 'fit-content' }}>
                + Create New Role
              </button>
              <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
                <table className="report-table">
                  <thead>
                    <tr>
                      <th>Role Name</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {roles.map(r => (
                      <tr key={r.name}>
                        <td><strong>{r.name}</strong></td>
                        <td>
                          <button className="ghost sm" onClick={() => handleEditRole(r)} style={{ marginRight: '10px', color: '#0f8a5f' }}>Edit</button>
                          {['admin', 'teacher', 'demo', 'student'].includes(r.name) ? null : (
                            <button className="ghost sm" onClick={() => deleteRole(r.name)}>Delete</button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="role-editor" style={{ background: '#f9fbfd', padding: '20px', borderRadius: '16px', border: '1px solid #e4ecf4' }}>
              <div style={{marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '8px'}}>
                <label style={{ fontWeight: '600' }}>Role Name</label>
                <input 
                  value={roleName} 
                  onChange={e => setRoleName(e.target.value)} 
                  disabled={!editingRole.isNew} 
                  placeholder="e.g., manager, guest"
                  style={{ maxWidth: '300px' }}
                />
              </div>
              <div style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
                <table className="report-table" style={{ background: 'white', borderRadius: '8px' }}>
                  <thead>
                    <tr>
                      <th style={{ background: '#e8eff6' }}>Module</th>
                      {PERMISSIONS.map(p => <th key={p} style={{ background: '#e8eff6', textTransform: 'capitalize' }}>{p}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {MODULES.map(mod => (
                      <tr key={mod}>
                        <td style={{ fontWeight: '600', color: '#4f6073' }}>{mod}</td>
                        {PERMISSIONS.map(perm => (
                          <td key={perm}>
                            <input 
                              type="checkbox"
                              style={{ width: 'auto', cursor: 'pointer' }}
                              checked={(rolePerms[mod] || []).includes(perm)}
                              onChange={() => togglePermission(mod, perm)}
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div style={{display: 'flex', gap: '1rem'}}>
                <button className="primary" onClick={saveRole}>Save Role Config</button>
                <button className="ghost" onClick={() => setEditingRole(null)}>Cancel</button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <h3>Member Assignments (Bulk)</h3>
          <p>Assign roles to multiple users at once, or view existing users grouped by role.</p>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Left side: Bulk Assign */}
            <div style={{ background: '#f9fbfd', padding: '20px', borderRadius: '16px', border: '1px solid #e4ecf4' }}>
              <h4 style={{ marginTop: 0, marginBottom: '12px' }}>Assign New Users</h4>
              <textarea 
                placeholder="Enter email addresses separated by commas or newlines" 
                value={assignEmails} 
                onChange={e => setAssignEmails(e.target.value)} 
                style={{ width: '100%', minHeight: '120px', padding: '12px', borderRadius: '12px', border: '1px solid #cdd8e3', marginBottom: '12px', fontFamily: 'inherit' }}
              />
              <div className="input-row">
                <select value={assignRole} onChange={e => setAssignRole(e.target.value)}>
                  <option value="">Select Role</option>
                  {roles.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
                </select>
                <button className="primary" onClick={saveAssignments}>Bulk Assign</button>
              </div>
            </div>

            {/* Right side: User List by Role */}
            <div style={{ background: '#ffffff', padding: '20px', borderRadius: '16px', border: '1px solid #e4ecf4', maxHeight: '500px', overflowY: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h4 style={{ margin: 0 }}>Current Users by Role</h4>
                <button 
                  className="ghost sm" 
                  onClick={deleteSelectedAssignments}
                  disabled={selectedEmails.length === 0}
                  style={{ color: selectedEmails.length > 0 ? 'red' : '#a0aec0', cursor: selectedEmails.length > 0 ? 'pointer' : 'not-allowed' }}
                >
                  Delete Selected ({selectedEmails.length})
                </button>
              </div>

              {Object.keys(assignmentsByRole).length === 0 ? (
                <p className="hint">No users currently assigned to roles.</p>
              ) : (
                Object.keys(assignmentsByRole).sort().map(role => (
                  <div key={role} style={{ marginBottom: '20px' }}>
                    <div style={{ background: '#e8eff6', padding: '6px 12px', borderRadius: '6px', fontWeight: 'bold', marginBottom: '8px', fontSize: '0.9rem', color: '#1b3a56' }}>
                      {role.toUpperCase()} <span style={{ fontWeight: 'normal', fontSize: '0.8rem', color: '#5b6b7c' }}>({assignmentsByRole[role].length})</span>
                    </div>
                    <ul className="list" style={{ gap: '4px' }}>
                      {assignmentsByRole[role].sort().map(email => (
                        <li key={email} style={{ padding: '8px 12px', background: 'white', border: '1px solid #edf2f7', display: 'flex', justifyContent: 'space-between' }}>
                          <span>{email}</span>
                          <input 
                            type="checkbox" 
                            style={{ width: 'auto', margin: 0 }}
                            checked={selectedEmails.includes(email)}
                            onChange={() => toggleEmailSelection(email)}
                          />
                        </li>
                      ))}
                    </ul>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
